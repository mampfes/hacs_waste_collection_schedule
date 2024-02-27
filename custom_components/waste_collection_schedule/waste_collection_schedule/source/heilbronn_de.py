from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Heilbronn Entsorgungsbetriebe"
DESCRIPTION = "Source for city of Heilbronn, Germany."
URL = "https://heilbronn.de"
TEST_CASES = {
    "Rosenau": {
        "plz": 74072,
        "strasse": "Rosenau",
        "hausnr": 33,
    },
    "Biberach": {
        "strasse": "Kehrhüttenstraße",
        "plz": 74078,
        "hausnr": "90",
    },
    "Klingenberg:": {
        "strasse": "Wittumhalde",
        "plz": "74081",
        "hausnr": 75,
    },
    "Klingenberg (hausnr as string):": {
        "strasse": "Wittumhalde",
        "plz": "74081",
        "hausnr": "75",
    },
    "Rosenbergstraße 53": {
        "strasse": "Rosenbergstraße",
        "plz": "74074",
        "hausnr": "50",
    },
    "Rosenbergstraße 41": {
        "strasse": "Rosenbergstraße",
        "plz": "74072",
        "hausnr": "41",
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
    def __init__(self, plz: int, strasse: str, hausnr: str | int | None = None):
        self._plz: str = str(plz)
        self._strasse: str = strasse
        self._hausnr: str | None = str(hausnr) if hausnr else None

    def fetch(self):
        r = requests.get(
            "https://api.heilbronn.de/garbage-calendar?method=get&datatype=districts"
        )
        r.raise_for_status()
        data = r.json()

        street = data["data"][self._plz][self._strasse]
        if not self._hausnr or "*" in street:
            if "*" not in street:
                raise ValueError(
                    f"Street {self._strasse} needs to be configured with a house number, available house numbers: {list(street.keys())}"
                )
            districts: dict = street["*"]
        else:
            if self._hausnr not in street:
                raise ValueError(
                    f"House number {self._hausnr} not found for street {self._strasse}, available house numbers: {list(street.keys())}"
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
