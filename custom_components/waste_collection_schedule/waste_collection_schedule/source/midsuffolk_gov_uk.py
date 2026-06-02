import datetime
import re
import time

import requests
from bs4 import BeautifulSoup

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentExceptionMultiple

TITLE = "Mid Suffolk District Council"
DESCRIPTION = "Source for Mid Suffolk District Council waste collection."
URL = "https://www.midsuffolk.gov.uk"
TEST_CASES = {
    "1 School Meadow Stowmarket": {
        "postcode": "IP14 2SA",
        "uprn": "10012168792",
    },
    "2 School Meadow Stowmarket": {
        "postcode": "IP14 2SA",
        "uprn": "10012168793",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "You need your postcode and UPRN. To find your UPRN, visit "
        "https://www.findmyaddress.co.uk or https://uprn.uk and search "
        "for your address. The UPRN is a unique number identifying your property."
    )
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "uprn": "UPRN (Unique Property Reference Number)",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Your full postcode, e.g. IP14 2SA",
        "uprn": "Your property's UPRN, e.g. 10012168792. Find it at https://uprn.uk",
    }
}

_BASE_URL = "https://www.midsuffolk.gov.uk/check-your-collection-day"
_PORTLET  = "_com_placecube_digitalplace_local_waste_portlet_CollectionDayFinderPortlet_"

ICON_MAP = {
    "refuse":    "mdi:trash-can",
    "recycling": "mdi:recycle",
    "paper":     "mdi:newspaper",
    "food":      "mdi:food-apple",
    "garden":    "mdi:leaf",
}


def _icon(waste_type: str) -> str:
    t = waste_type.lower()
    for key, icon in ICON_MAP.items():
        if key in t:
            return icon
    return "mdi:trash-can"


class Source:
    def __init__(self, postcode: str, uprn: str):
        self._postcode = postcode.strip().lower()
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        # Build the query string exactly as the browser does
        params = {
            "p_p_id": "com_placecube_digitalplace_local_waste_portlet_CollectionDayFinderPortlet",
            "p_p_lifecycle": "0",
            "p_p_state": "normal",
            "p_p_mode": "view",
            _PORTLET + "mvcRenderCommandName": "/collection_day_finder/get_days",
        }

        # Form data fields
        data = {
            _PORTLET + "formDate":    str(int(time.time() * 1000)),
            _PORTLET + "postcode":    self._postcode,
            _PORTLET + "uprn":        self._uprn,
            _PORTLET + "fullAddress": "",
        }

        response = session.post(_BASE_URL, params=params, data=data, timeout=30)
        response.raise_for_status()

        return self._parse(response.text)

    def _parse(self, html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")
        entries: list[Collection] = []

        # The page returns a table with columns:
        # Collection type | Next collection | Frequency
        for row in soup.select("table tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            waste_type = cells[0].get_text(strip=True)
            date_text  = cells[1].get_text(strip=True)

            if not waste_type or not date_text:
                continue

            date = _parse_date(date_text)
            if date:
                entries.append(
                    Collection(
                        date=date,
                        t=waste_type,
                        icon=_icon(waste_type),
                    )
                )

        if not entries:
            raise SourceArgumentExceptionMultiple(
                ["postcode", "uprn"],
                "No collection dates found. Check your UPRN and postcode are correct. "
                f"postcode={self._postcode}, uprn={self._uprn}",
            )

        return entries


_DATE_FORMATS = (
    "%A %d %B %Y",   # Thursday 04 Jun 2026 — note: need %b not %B for abbrev
    "%A %d %b %Y",   # Thursday 04 Jun 2026
    "%d %B %Y",
    "%d %b %Y",
    "%d/%m/%Y",
    "%Y-%m-%d",
)


def _parse_date(text: str) -> datetime.date | None:
    text = text.strip()
    # Remove ordinal suffixes: 1st, 2nd, 3rd, 4th etc
    text = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", text)
    for fmt in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None
