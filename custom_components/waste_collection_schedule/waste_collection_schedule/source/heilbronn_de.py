from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Heilbronn Entsorgungsbetriebe"
TITLE_LANG = "de"
DESCRIPTION = "Source for city of Heilbronn, Germany."
DESCRIPTION_LANG = "de"
URL = "https://heilbronn.de"
TEST_CASES = {
    "Rosenau": {
        "postcode": 74072,
        "street": "Rosenau",
        "house_number": 33,
    },
    "Biberach": {
        "street": "Kehrhüttenstraße",
        "postcode": 74078,
        "house_number": "90",
    },
    "Klingenberg:": {
        "street": "Wittumhalde",
        "postcode": "74081",
        "house_number": 75,
    },
    "Klingenberg (house_number as string):": {
        "street": "Wittumhalde",
        "postcode": "74081",
        "house_number": "75",
    },
    "Rosenbergstraße 53": {
        "street": "Rosenbergstraße",
        "postcode": "74074",
        "house_number": "50",
    },
    "Rosenbergstraße 41": {
        "street": "Rosenbergstraße",
        "postcode": "74072",
        "house_number": "41",
    },
}

ICON_MAP = {
    "residual": "mdi:trash-can",
    "bio": "mdi:leaf",
    "green": "mdi:leaf",
    "light-packaging": "mdi:recycle",
    "paper": "mdi:package-variant",
    "paper-bundle": "mdi:package-variant",
    "christmastree": "mdi:pine-tree",
}


class Source:
    def __init__(
        self, postcode: int, street: str, house_number: str | int | None = None
    ):
        self._plz: str = str(postcode)
        self._strasse: str = street
        self._hausnr: str | None = str(house_number) if house_number else None

    def fetch(self):
        r = requests.get(
            "https://api.heilbronn.de/garbage-calendar?method=get&datatype=districts"
        )
        r.raise_for_status()
        data = r.json()

        street = data["data"][self._plz][self._strasse]
        if not self._hausnr or "*" in street:
            if "*" not in street:
                raise SourceArgumentRequiredWithSuggestions(
                    "house_number",
                    "is required for this street",
                    suggestions=street.keys(),
                )
                raise ValueError(
                    f"Street {self._strasse} needs to be configured with a house number, available house numbers: {list(street.keys())}"
                )
            districts: dict = street["*"]
        else:
            if self._hausnr not in street:
                raise SourceArgumentNotFoundWithSuggestions(
                    "house_number",
                    self._hausnr,
                    suggestions=street.keys(),
                )
            districts: dict = street[self._hausnr]

        # filter waste type
        collection_keys = {
            value for key, value in districts.items() if key not in ("city", "district")
        }

        r = requests.get(
            "https://api.heilbronn.de/garbage-calendar?method=get&datatype=pickupdates"
        )
        r.raise_for_status()
        pickupDates = r.json()

        entries = []

        for valueDistrict in collection_keys:
            value = pickupDates["data"][valueDistrict]
            for collection_type, collection_dates in value.items():
                for value2 in collection_dates.values():
                    date = datetime.strptime(value2, "%Y-%m-%d").date()
                    entry = collection_type
                    icon = ICON_MAP.get(entry.split("_")[0].lower())
                    entries.append(Collection(date, entry, icon))
        return entries
