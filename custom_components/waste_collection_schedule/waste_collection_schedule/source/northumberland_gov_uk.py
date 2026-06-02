import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Northumberland County Council"
DESCRIPTION = "Source for Northumberland County Council waste collection schedule."
URL = "https://www.northumberland.gov.uk"
COUNTRY = "uk"
TEST_CASES = {
    "30, NE46 1UF (UPRN 100110637553)": {"uprn": "100110637553"},
}

ICON_MAP = {
    "general": Icons.GENERAL_WASTE,
    "refuse": Icons.GENERAL_WASTE,
    "black": Icons.GENERAL_WASTE,
    "recycl": Icons.RECYCLING,
    "blue": Icons.RECYCLING,
    "garden": Icons.GARDEN,
    "green": Icons.GARDEN,
    "brown": Icons.GARDEN,
    "food": Icons.BIO_KITCHEN,
    "glass": Icons.GLASS,
}

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://bincollection.northumberland.gov.uk"

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "UPRN",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN) for your address.",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://bincollection.northumberland.gov.uk/postcode, enter your postcode and select your address. The UPRN is the number shown in the address dropdown value, or find it at https://www.findmyaddress.co.uk/.",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        # Step 1: GET the postcode page to establish a session and retrieve the CSRF token
        r1 = session.get(f"{BASE_URL}/postcode")
        r1.raise_for_status()

        soup1 = BeautifulSoup(r1.text, "html.parser")
        csrf_input = soup1.find("input", {"name": "_csrf"})
        if csrf_input is None:
            raise ValueError(
                "Could not find CSRF token on the postcode page. The site may have changed."
            )
        csrf_token = csrf_input.get("value", "")

        # Step 2: POST to /address-select with the CSRF token and the UPRN
        r2 = session.post(
            f"{BASE_URL}/address-select",
            data={
                "_csrf": csrf_token,
                "address": self._uprn,
            },
            allow_redirects=True,
        )
        r2.raise_for_status()

        return self._parse_schedule(r2.text)

    def _parse_schedule(self, html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")

        entries = []

        # The bincollection.* sites typically render bin cards as div.card or div.service-item
        # containing a heading/title for bin type and a date element.
        # Try multiple known patterns from this site family.

        # Pattern A: card h-100 divs (same family as newham_gov_uk)
        cards = soup.find_all("div", class_=re.compile(r"\bcard\b"))
        for card in cards:
            # Extract bin type from header
            header = card.find(
                ["h2", "h3", "h4", "h5", "b", "strong"],
            )
            if header is None:
                continue
            bin_type = header.get_text(strip=True)
            if not bin_type:
                continue

            # Extract date — look for <p>, <span>, <mark> or similar with a date
            date_text = None
            for tag in card.find_all(["p", "span", "mark", "td", "dd"]):
                text = tag.get_text(strip=True)
                # Match date patterns: "12 January 2025", "12/01/2025", "Monday 12 January 2025"
                if re.search(r"\d{1,2}[\s/]\w+[\s/]\d{4}|\d{1,2}/\d{2}/\d{4}", text):
                    date_text = text
                    break

            if date_text is None:
                continue

            date = _parse_date(date_text)
            if date is None:
                _LOGGER.warning(
                    "Could not parse date %r for bin type %r", date_text, bin_type
                )
                continue

            icon = _get_icon(bin_type)
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        if entries:
            return entries

        # Pattern B: table rows with bin type and date columns
        rows = soup.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            bin_type = cells[0].get_text(strip=True)
            date_text = cells[1].get_text(strip=True)
            date = _parse_date(date_text)
            if date is None:
                continue
            icon = _get_icon(bin_type)
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        if entries:
            return entries

        # Pattern C: definition list (dt/dd pairs)
        dts = soup.find_all("dt")
        for dt in dts:
            bin_type = dt.get_text(strip=True)
            dd = dt.find_next_sibling("dd")
            if dd is None:
                continue
            date_text = dd.get_text(strip=True)
            date = _parse_date(date_text)
            if date is None:
                continue
            icon = _get_icon(bin_type)
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        if not entries:
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                "No collection data found. Please check your UPRN is correct.",
            )

        return entries


def _parse_date(text: str):
    """Attempt to parse a date from a string using common UK formats."""
    # Strip leading day name if present: "Monday 12 January 2025"
    text = re.sub(
        r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = text.strip()

    for fmt in (
        "%d %B %Y",  # "12 January 2025"
        "%d %b %Y",  # "12 Jan 2025"
        "%d/%m/%Y",  # "12/01/2025"
        "%Y-%m-%d",  # "2025-01-12"
    ):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _get_icon(bin_type: str):
    lower = bin_type.lower()
    for keyword, icon in ICON_MAP.items():
        if keyword in lower:
            return icon
    return None
