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
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)

TITLE = "Mid Devon District Council"
DESCRIPTION = "Source for waste collection services for Mid Devon District Council"
URL = "https://www.middevon.gov.uk"

TEST_CASES = {
    "Bradninch": {"uprn": 100040359199},
    "Bradninch - string": {"uprn": "100040359199"},
    "Cullompton": {"uprn": 100040354099},
}

ICON_MAP = {
    "recycl": "mdi:recycle",
    "garden": "mdi:leaf",
    "food": "mdi:food-apple",
    "caddy": "mdi:food-apple",
    "rubbish": "mdi:trash-can",
    "refuse": "mdi:trash-can",
    "domestic": "mdi:trash-can",
    "black": "mdi:trash-can",
}
DEFAULT_ICON = "mdi:trash-can"

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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}


class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(HEADERS)

        session_id = self._get_auth_session(session)
        rows = self._fetch_lookup_rows(session, session_id)
        rows = self._fetch_lookup_rows(session, session_id)
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

        # Prefer API format: display (date) + CollectionItems (type names)
        if "display" in first_row and "CollectionItems" in first_row:
            entries = self._parse_api_collection_rows(rows)
            if entries:
                return entries

        return self._parse_lookup_rows(rows)

    def _get_auth_session(self, session: requests.Session) -> str:
        """Establish session and return auth-session token."""
        response = session.get(FORM_PAGE_URL, timeout=30)
        response.raise_for_status()

        sid = self._extract_auth_session_from_page(response.text)
        if not sid:
            auth = session.get(AUTH_URL)
            auth.raise_for_status()
            sid = auth.json().get("auth-session")
        if not sid:
            raise SourceArgumentException(
                "uprn",
                "Could not establish session with council form.",
            )
        return sid

    def _fetch_lookup_rows(self, session: requests.Session, session_id: str) -> dict:
        """Submit UPRN via runLookup and return rows_data."""
        now = time.time_ns() // 1_000_000
        lookup_url = f"{RUN_LOOKUP_BASE}&_={now}&sid={session_id}"
        payload = {
            "formValues": {
                "Section 1": {
                    "UPRN": {"name": "UPRN", "value": self._uprn},
                    "listAddress": {"name": "listAddress", "value": self._uprn},
                }
            }
        }
        response = session.post(lookup_url, json=payload, timeout=30)
        response.raise_for_status()

        try:
            data = response.json()
            rows = (
                data.get("integration", {}).get("transformed", {}).get("rows_data")
                or {}
            )
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
        return rows

    def _extract_auth_session_from_page(self, html: str) -> str | None:
        """Extract auth-session from the form page script (FS.FormDefinition.data.session)."""
        match = re.search(
            r'["\']auth-session["\']\s*:\s*["\']([^"\']+)["\']',
            html,
        )
        return match.group(1) if match else None

    def _icon_for_type(self, waste_type: str) -> str:
        waste_lower = waste_type.lower()

        for keyword, icon in ICON_MAP.items():
            if keyword in waste_lower:
                return icon

        return DEFAULT_ICON

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

            try:
                dt = datetime.strptime(date_str, "%d-%b-%y").date()
            except ValueError:
                continue
            # Split "Blue Food Caddy and Black & Green Recycling Boxes" into separate types
            for part in re.split(r"\s+(?:and|&)\s+", items_str, flags=re.I):
                part = part.strip()
                if not part:
                    continue
                key = (dt, part)
                if key in seen:
                    continue
                seen.add(key)
                entries.append(
                    Collection(
                        date=dt,
                        t=part,
                        icon=self._icon_for_type(part),
                    )
                )
        return entries

    def _parse_lookup_rows(self, rows: dict) -> list[Collection]:
        """Parse lookup rows with CollectionDay and display (date) fields."""
        entries = []
        seen = set()
        for row in rows.values():
            if not isinstance(row, dict):
                continue
            date_str = row.get("display")
            if not date_str:
                continue

            try:
                dt = datetime.strptime(date_str, "%d-%b-%y").date()
            except ValueError:
                continue

            collection_day = row.get("CollectionDay", "")
            key = (dt, collection_day)
            if key in seen:
                continue
            seen.add(key)
            entries.append(
                Collection(
                    date=dt,
                    t=collection_day,
                    icon=self._icon_for_type(collection_day),
                )
            )
        return entries
