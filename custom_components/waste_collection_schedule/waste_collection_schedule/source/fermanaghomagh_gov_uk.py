from datetime import datetime

import bs4
import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

# Title will show up in README.md and info.md
TITLE = "Fermanagh and Omagh District Council"
# Describe your source
DESCRIPTION = "Source for the Fermanagh and Omagh District Council, Northern Ireland"
# Insert url to service homepage. URL will show up in README.md and info.md
URL = "https://www.fermanaghomagh.com/"
TEST_CASES = {
    "Test_001": {"postcode": "BT78 1RG", "house_number": "1"},
    "Test_002": {"postcode": "BT78 5AA", "house_number": "10"},
    "Test_003": {"property_id": "GMtpf6Tk1glK57Zj"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "property_id": "Property ID",
        "postcode": "Postcode",
        "house_number": "House Number",
    },
    "de": {
        "property_id": "Grundstücks-ID",
        "postcode": "Postleitzahl",
        "house_number": "Hausnummer",
    },
}
PARAM_DESCRIPTIONS = {
    "en": {
        "property_id": "The property ID as found in the URL when looking up your bin collection days",
        "postcode": "The postcode of the property, e.g. BT78 1RG",
        "house_number": "The house number (or name) of the property",
    },
    "de": {
        "property_id": "Die Grundstücks-ID, die in der URL bei der Suche nach den Abholtagen zu finden ist",
        "postcode": "Die Postleitzahl des Grundstücks, z.B. BT78 1RG",
        "house_number": "Die Hausnummer (oder der Hausname) des Grundstücks",
    },
}

API_URL = "https://fermanaghomagh.isl-fusion.com"
ICON_MAP = {
    "Black Landfill": Icons.GENERAL_WASTE,
    "Blue Recycling": Icons.RECYCLING,
    "Brown Composting": Icons.GARDEN,
    "Food": Icons.BIO_KITCHEN,
}

SOURCE_CODEOWNERS = ["@bbr111"]


class Source:
    def __init__(self, property_id=None, postcode=None, house_number=None):
        self._property_id = property_id
        self._postcode = postcode
        self._house_number = str(house_number) if house_number is not None else None

        if not any([self._property_id, self._postcode and self._house_number]):
            errors = []
            if self._postcode:
                errors.append("house_number")
            elif self._house_number:
                errors.append("postcode")
            else:
                errors = ["property_id", "postcode", "house_number"]

            raise SourceArgumentExceptionMultiple(
                errors,
                "Must provide either a property ID or both the Postcode and House Number",
            )

    def fetch(self):
        session = requests.Session()

        if not self._property_id:
            search_url = f"{API_URL}/address/{self._postcode}"
            response = session.get(search_url)
            response.raise_for_status()
            try:
                address_list = response.json().get("html")
            except Exception:
                raise SourceArgumentNotFound("postcode", self._postcode) from None

            soup = bs4.BeautifulSoup(address_list, features="html.parser")

            property_id_by_house_number = {}
            for li in soup.findAll("li"):
                link = li.findAll("a")[0]
                property_id = link.attrs["href"].replace("/view", "").replace("/", "")
                address = link.text
                house_number = address.split(" ", 1)[0]
                property_id_by_house_number[house_number] = property_id

            self._property_id = property_id_by_house_number.get(self._house_number)

            if not self._property_id:
                raise SourceArgumentNotFoundWithSuggestions(
                    "house_number",
                    self._house_number,
                    property_id_by_house_number.keys(),
                )

        today = datetime.today().date()
        calendar_url = (
            f"{API_URL}/calendar/{self._property_id}/{today.strftime('%Y-%m-%d')}"
        )
        response = session.get(calendar_url)
        response.raise_for_status()

        try:
            next_collections = response.json().get("nextCollections")
            collections_by_date = next_collections["collections"]
        except Exception:
            raise ValueError("No collection data in response") from None

        entries = []  # List that holds collection schedule

        for collection in collections_by_date.values():
            collection_date = datetime.strptime(collection["date"], "%Y-%m-%d").date()

            for bin in collection["collections"].values():
                entries.append(
                    Collection(
                        date=collection_date,
                        t=bin["name"],
                        icon=ICON_MAP.get(bin["name"]),
                    )
                )

        return entries
