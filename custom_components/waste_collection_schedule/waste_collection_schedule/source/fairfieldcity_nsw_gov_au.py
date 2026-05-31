from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Fairfield City Council"
DESCRIPTION = "Source for Fairfield City Council bin collection, NSW, Australia."
URL = "https://kerbside.fairfieldcity.nsw.gov.au/kerbside/"
COUNTRY = "au"
TEST_CASES = {
    "1 Dawson ST, FAIRFIELD HEIGHTS": {
        "street_number": "1",
        "street_and_suburb": "Dawson ST, FAIRFIELD HEIGHTS",
    },
    "12 Zadro AVE, BOSSLEY PARK": {
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


class Source:
    def __init__(self, street_number: str, street_and_suburb: str):
        self._street_number = str(street_number).strip()
        self._street_and_suburb = street_and_suburb.strip()

    def fetch(self) -> list[Collection]:
        response = requests.post(
            API_URL,
            data={
                "myStreetNumber": self._street_number,
                "myStreetAndSuburb": self._street_and_suburb,
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
