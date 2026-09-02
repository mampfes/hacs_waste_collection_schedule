import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Fairfield City Council"
DESCRIPTION = "Source for Fairfield City Council bin collection, NSW, Australia."
URL = "https://kerbside.fairfieldcity.nsw.gov.au/kerbside/"
COUNTRY = "au"
TEST_CASES = {
    "1 Dawson Street, FAIRFIELD HEIGHTS": {
        "street_number": "1",
        "street_and_suburb": "Dawson Street, FAIRFIELD HEIGHTS",
    },
    "12 Zadro Avenue, BOSSLEY PARK": {
        "street_number": "12",
        "street_and_suburb": "Zadro Avenue, BOSSLEY PARK",
    },
    # Abbreviated street types: what the council's autocomplete used to emit,
    # and therefore what most existing configurations still contain.
    "1 Dawson ST, FAIRFIELD HEIGHTS (abbreviated)": {
        "street_number": "1",
        "street_and_suburb": "Dawson ST, FAIRFIELD HEIGHTS",
    },
    "12 Zadro AVE, BOSSLEY PARK (abbreviated)": {
        "street_number": "12",
        "street_and_suburb": "Zadro AVE, BOSSLEY PARK",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit https://kerbside.fairfieldcity.nsw.gov.au/kerbside/ and start typing "
        "your street name and suburb into the 'Street name & Suburb' field. "
        "Use the autocomplete suggestion (e.g. 'Dawson ST, FAIRFIELD HEIGHTS') "
        "as the value for street_and_suburb, and enter just your street number "
        "for street_number."
    )
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_number": "Street Number",
        "street_and_suburb": "Street Name & Suburb",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_number": "Your street number (e.g. 1, 7A, 7/10).",
        "street_and_suburb": (
            "Street name and suburb as shown in the autocomplete list "
            "(e.g. 'Dawson ST, FAIRFIELD HEIGHTS')."
        ),
    }
}

ICON_MAP = {
    "Red bin": Icons.GENERAL_WASTE,
    "Yellow bin": Icons.RECYCLING,
    "Green bin": Icons.ORGANIC,
}

API_URL = "https://kerbside.fairfieldcity.nsw.gov.au/kerbside/"
# The council's own autocomplete list. The form only answers for a value taken
# verbatim from it, and the list was switched from abbreviated street types
# ("Dawson ST") to spelled-out ones ("Dawson Street"), which silently broke
# every previously valid saved value.
AUTOCOMPLETE_URL = f"{API_URL}fcc-autocomplete.js"
AUTOCOMPLETE_ARRAY = "arrAddressStreetAndSuburb"

# Street-type abbreviations seen in the old list and in what people type.
STREET_TYPES = {
    "AV": "AVENUE",
    "AVE": "AVENUE",
    "BVD": "BOULEVARD",
    "CCT": "CIRCUIT",
    "CH": "CHASE",
    "CL": "CLOSE",
    "CR": "CRESCENT",
    "CRES": "CRESCENT",
    "CT": "COURT",
    "DR": "DRIVE",
    "ESP": "ESPLANADE",
    "GDNS": "GARDENS",
    "GR": "GROVE",
    "GRV": "GROVE",
    "HWY": "HIGHWAY",
    "LN": "LANE",
    "LP": "LOOP",
    "PDE": "PARADE",
    "PKWY": "PARKWAY",
    "PL": "PLACE",
    "RD": "ROAD",
    "RSE": "RISE",
    "SQ": "SQUARE",
    "ST": "STREET",
    "TCE": "TERRACE",
    "WY": "WAY",
}


def _canonical(value: str) -> str:
    """Upper-case, collapse whitespace and expand street-type abbreviations.

    Comparing on this lets a stored "Dawson ST, FAIRFIELD HEIGHTS" match the
    list's current "Dawson Street, FAIRFIELD HEIGHTS", and vice versa.
    """
    words = re.split(r"(\W+)", value.upper())
    return "".join(STREET_TYPES.get(w, w) for w in words).strip()


class Source:
    def __init__(self, street_number: str, street_and_suburb: str):
        self._street_number = str(street_number).strip()
        self._street_and_suburb = street_and_suburb.strip()

    def _known_streets(self, session: requests.Session) -> list[str]:
        response = session.get(AUTOCOMPLETE_URL, timeout=30)
        response.raise_for_status()
        match = re.search(
            AUTOCOMPLETE_ARRAY + r"\s*=\s*\[(.*?)\]", response.text, re.DOTALL
        )
        if not match:
            return []
        return re.findall(r'"([^"]+)"', match.group(1))

    def _resolve_street_and_suburb(self, session: requests.Session) -> str:
        streets = self._known_streets(session)
        if not streets:
            # Autocomplete unavailable or restructured; send what we were given
            # rather than refusing outright.
            return self._street_and_suburb
        wanted = _canonical(self._street_and_suburb)
        for street in streets:
            if _canonical(street) == wanted:
                return street
        raise SourceArgumentNotFoundWithSuggestions(
            "street_and_suburb", self._street_and_suburb, streets
        )

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        street_and_suburb = self._resolve_street_and_suburb(session)

        response = session.post(
            API_URL,
            data={
                "myStreetNumber": self._street_number,
                "myStreetAndSuburb": street_and_suburb,
            },
            timeout=30,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        results_area = soup.find("div", id="fcc-results-area")
        if results_area is None:
            raise SourceArgumentNotFound(
                "street_and_suburb",
                self._street_and_suburb,
            )

        entries: list[Collection] = []
        seen_types: set[str] = set()

        for p in results_area.find_all("p"):
            img = p.find("img")
            strong = p.find("strong")
            if img is None or strong is None:
                continue

            bin_type = img.get("alt", "").strip()
            if not bin_type or bin_type in seen_types:
                continue

            date_text = strong.get_text(strip=True)
            try:
                collection_date = datetime.strptime(date_text, "%A, %d/%m/%Y").date()
            except ValueError:
                continue

            seen_types.add(bin_type)
            entries.append(
                Collection(
                    date=collection_date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        if not entries:
            raise SourceArgumentNotFound(
                "street_and_suburb",
                self._street_and_suburb,
            )

        return entries
