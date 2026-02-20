"""
Mid Devon District Council - Collection Day Lookup.

Retrieves collection schedules from the council's Collection Day Lookup API.
Gets session from the form page, submits UPRN via runLookup (id=642315aacb919),
and parses the response (CollectionDay, display, CollectionItems). Falls back
to fetching the calendar page and scraping HTML if the API returns a different format.
"""

import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)

TITLE = "Mid Devon District Council"
DESCRIPTION = (
    "Source for waste collection services for Mid Devon District Council"
)
URL = "https://www.middevon.gov.uk"

TEST_CASES = {
    "Bradninch": {"uprn": 100040359199},
    "Bradninch - string": {"uprn": "100040359199"},
}

ICON_MAP = {
    "Domestic": "mdi:trash-can",
    "Food": "mdi:food-apple",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
    "Rubbish": "mdi:trash-can",
    "Refuse": "mdi:trash-can",
}

# Collection Day Lookup form (same as council's "Check collection dates" page)
FORM_PAGE_URL = (
    "https://my.middevon.gov.uk/en/AchieveForms/"
    "?form_uri=sandbox-publish://AF-Process-2289dd06-9a12-4202-ba09-857fe756f6bd/"
    "AF-Stage-eb382015-001c-415d-beda-84f796dbb167/definition.json"
    "&redirectlink=%2Fen&cancelRedirectLink=%2Fen&consentMessage=yes"
)
AUTH_URL = (
    "https://my.middevon.gov.uk/authapi/isauthenticated"
    "?uri=https%253A%252F%252Fmy.middevon.gov.uk%252Fen%252FAchieveForms%252F"
    "%253Fform_uri%253Dsandbox-publish%253A%252F%252FAF-Process-2289dd06-9a12-4202-ba09-857fe756f6bd%252F"
    "AF-Stage-eb382015-001c-415d-beda-84f796dbb167%252Fdefinition.json"
    "%2526redirectlink%253D%25252Fen%2526cancelRedirectLink%253D%25252Fen%2526consentMessage%253Dyes"
    "&hostname=my.middevon.gov.uk&withCredentials=true"
)
RUN_LOOKUP_BASE = (
    "https://my.middevon.gov.uk/apibroker/runLookup"
    "?id=642315aacb919&repeat_against=&noRetry=false&getOnlyTokens=undefined"
    "&log_id=&app_name=AF-Renderer::Self"
)
BASE_URL = "https://my.middevon.gov.uk"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}


class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        s.headers.update(HEADERS)

        # 1) Open the Collection Day Lookup form page (establishes session)
        r = s.get(FORM_PAGE_URL)
        r.raise_for_status()

        # 2) Get auth session key from the form page (scraped from FS.FormDefinition in script)
        #    or fallback to authapi. Page has: FS.FormDefinition = {"fillform-frame-1":{"data":{"session":{"auth-session":"..."}}}}
        sid = self._extract_auth_session_from_page(r.text)
        if not sid:
            auth = s.get(AUTH_URL)
            auth.raise_for_status()
            sid = auth.json().get("auth-session")
        if not sid:
            raise SourceArgumentException(
                "uprn",
                "Could not establish session with council form.",
            )

        # 3) Submit UPRN via the form's runLookup (same request the form makes)
        now = time.time_ns() // 1_000_000
        lookup_url = f"{RUN_LOOKUP_BASE}&_={now}&sid={sid}"
        # API tokens include {listAddress}; some lookups expect listAddress or UPRN
        payload = {
            "formValues": {
                "Section 1": {
                    "UPRN": {"name": "UPRN", "value": self._uprn},
                    "listAddress": {"name": "listAddress", "value": self._uprn},
                }
            }
        }
        lookup_resp = s.post(lookup_url, json=payload)
        lookup_resp.raise_for_status()

        try:
            data = lookup_resp.json()
            rows = data.get("integration", {}).get("transformed", {}).get("rows_data") or {}
        except Exception as e:
            raise SourceArgumentException(
                "uprn",
                f"Council lookup returned invalid response: {e}",
            )

        if not rows:
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                "no collection data returned for this address.",
            )

        first_row = next(iter(rows.values()))
        if not isinstance(first_row, dict):
            raise SourceArgumentException(
                "uprn",
                "Council lookup returned unexpected data format.",
            )

        # 4) API format: CollectionDay, display (date), CollectionItems (type names)
        #    e.g. display="23-Feb-26", CollectionItems="Blue Food Caddy and Black & Green Recycling Boxes"
        if "display" in first_row and "CollectionItems" in first_row:
            entries = self._parse_api_collection_rows(rows)
            if entries:
                return entries

        # 5) Legacy: calendar link in response (wcs_GranicusURL) – fetch and scrape
        calendar_path = (
            first_row.get("wcs_GranicusURL")
            or first_row.get("Wcs_GranicusURL")
            or first_row.get("granicusurl")
        )
        if calendar_path:
            if calendar_path.startswith("/"):
                calendar_url = BASE_URL + calendar_path
            else:
                calendar_url = calendar_path
            page_resp = s.get(calendar_url)
            page_resp.raise_for_status()
            entries = self._parse_result_page(page_resp.text)
            if entries:
                return entries

        return self._parse_lookup_rows(rows)

    def _extract_auth_session_from_page(self, html: str):
        """Extract auth-session from the form page script (FS.FormDefinition.data.session)."""
        # Match: "auth-session":"2bj6rc37dlmmhvj3e1fe96vp03" or 'auth-session':'...'
        m = re.search(
            r'["\']auth-session["\']\s*:\s*["\']([^"\']+)["\']',
            html,
        )
        return m.group(1) if m else None

    def _parse_result_page(self, html: str) -> list[Collection]:
        """Extract collection dates and types from the form result/calendar page HTML."""
        soup = BeautifulSoup(html, "html.parser")
        seen = set()
        entries = []

        for tag in soup(["script", "style"]):
            tag.decompose()
        # Ignore download calendar button/link so it is not parsed as a collection
        for tag in soup.find_all(["a", "button"]):
            if re.search(r"download\s*calendar", tag.get_text(strip=True), re.I):
                tag.decompose()

        def add_entry(date_val, type_val):
            key = (date_val, type_val)
            if key in seen:
                return
            seen.add(key)
            entries.append(
                Collection(
                    date=date_val,
                    t=type_val,
                    icon=self._icon_for_type(type_val),
                )
            )

        # Mid Devon specific: .bin-dates .bin-item .collection-details with "Date: DD-Mon-YY"
        for details in soup.find_all("div", class_="collection-details"):
            divs = details.find_all("div", recursive=False)
            type_val = None
            date_val = None
            for div in divs:
                text = div.get_text(strip=True)
                if not text:
                    continue
                # "Date: 23-Feb-26" or "Date: 02-Mar-26"
                date_match = re.search(r"Date:\s*(\d{1,2}-[A-Za-z]{3}-\d{2,4})", text, re.I)
                if date_match:
                    date_val = self._parse_date(date_match.group(1))
                else:
                    # Waste type is in <strong> e.g. "Your next Blue Food Caddy Collection"
                    strong = div.find("strong")
                    if strong and "date:" not in text.lower()[:15]:
                        type_val = strong.get_text(strip=True)
            if date_val and type_val:
                add_entry(date_val, type_val)

        if entries:
            return entries

        date_pattern = re.compile(
            r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})"
            r"|(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\s+\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}",
            re.I,
        )
        waste_keywords = re.compile(
            r"\b(rubbish|refuse|recycling|recycle|garden|food|domestic|general|black\s*bin|green\s*bin|blue\s*bin|brown\s*bin|caddy)\b",
            re.I,
        )

        # Tables: rows with both date and waste type
        for table in soup.find_all("table"):
            for tr in table.find_all("tr"):
                text = tr.get_text(separator=" ", strip=True)
                if not waste_keywords.search(text) or not date_pattern.search(text):
                    continue
                date_val = self._parse_date(text)
                type_val = None
                for cell in tr.find_all(["td", "th"]):
                    cell_text = cell.get_text(strip=True)
                    if waste_keywords.search(cell_text):
                        type_val = cell_text
                        break
                if type_val and date_val:
                    add_entry(date_val, type_val)
                elif date_val:
                    m = waste_keywords.search(text)
                    add_entry(date_val, m.group(0).strip() if m else "Collection")

        # List items / divs with collection-related class
        for tag in soup.find_all(["li", "div"], class_=re.compile(r"collection|day|date|schedule", re.I)):
            text = tag.get_text(separator=" ", strip=True)
            if not date_pattern.search(text) or not waste_keywords.search(text):
                continue
            date_val = self._parse_date(text)
            if not date_val:
                continue
            m = waste_keywords.search(text)
            add_entry(date_val, m.group(0).strip() if m else "Collection")

        return entries

    def _parse_date(self, text: str):
        """Try to parse a date from text. Returns date or None."""
        text = text.strip()
        # DD-MMM-YY or DD-MMM-YYYY (e.g. 23-Feb-26, 02-Mar-26)
        m = re.search(
            r"(\d{1,2})-([A-Za-z]{3})-(\d{2,4})\b",
            text,
        )
        if m:
            months = "jan feb mar apr may jun jul aug sep oct nov dec".split()
            try:
                mo = months.index(m.group(2).lower()[:3]) + 1
                y = int(m.group(3))
                if y < 100:
                    y += 2000
                return datetime(y, mo, int(m.group(1))).date()
            except (ValueError, IndexError):
                pass
        # DD/MM/YYYY or DD-MM-YYYY (numeric)
        m = re.search(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})", text)
        if m:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if y < 100:
                y += 2000
            try:
                return datetime(y, mo, d).date()
            except ValueError:
                pass
        # DD Month YYYY
        m = re.search(
            r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{2,4})",
            text,
            re.I,
        )
        if m:
            months = "jan feb mar apr may jun jul aug sep oct nov dec".split()
            try:
                mo = months.index(m.group(2).lower()[:3]) + 1
                y = int(m.group(3))
                if y < 100:
                    y += 2000
                return datetime(y, mo, int(m.group(1))).date()
            except (ValueError, IndexError):
                pass
        return None

    def _icon_for_type(self, waste_type: str):
        waste_lower = waste_type.lower()
        if "recycl" in waste_lower:
            return ICON_MAP.get("Recycling")
        if "garden" in waste_lower or "green" in waste_lower:
            return ICON_MAP.get("Garden")
        if "food" in waste_lower or "caddy" in waste_lower:
            return ICON_MAP.get("Food")
        if "rubbish" in waste_lower or "refuse" in waste_lower or "domestic" in waste_lower or "black" in waste_lower:
            return ICON_MAP.get("Domestic")
        return ICON_MAP.get("Domestic")

    def _parse_api_collection_rows(self, rows: dict) -> list[Collection]:
        """Parse API rows with CollectionDay, display (date), CollectionItems.
        CollectionItems may list multiple types separated by ' and ' (e.g. one date, Food + Recycling).
        """
        entries = []
        seen = set()
        for row in rows.values():
            if not isinstance(row, dict):
                continue
            # display = date (e.g. 23-Feb-26); CollectionDay = day name (e.g. Monday)
            date_str = row.get("display")
            items_str = row.get("CollectionItems") or ""
            if not date_str:
                continue
            date_val = self._parse_date(str(date_str))
            if not date_val:
                continue
            # Split "Blue Food Caddy and Black & Green Recycling Boxes" into separate types
            for part in re.split(r"\s+and\s+", items_str, flags=re.I):
                part = part.strip()
                if not part:
                    continue
                key = (date_val, part)
                if key in seen:
                    continue
                seen.add(key)
                entries.append(
                    Collection(
                        date=date_val,
                        t=part,
                        icon=self._icon_for_type(part),
                    )
                )
        return entries

    def _parse_lookup_rows(self, rows: dict) -> list[Collection]:
        """Fallback: build entries from lookup API rows (e.g. StartDate only)."""
        entries = []
        for row in rows.values():
            if not isinstance(row, dict):
                continue
            date_str = row.get("StartDate") or row.get("display")
            if not date_str or not re.search(r"[\d\-/]", str(date_str)):
                continue
            date_val = self._parse_date(str(date_str))
            if not date_val:
                continue
            entries.append(
                Collection(
                    date=date_val,
                    t="Calendar",
                    icon=ICON_MAP.get("Domestic"),
                )
            )
        return entries
