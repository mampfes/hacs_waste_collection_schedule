from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

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
        "hausnr": "53",
    },
    "Rosenbergstraße 41": {
        "strasse": "Rosenbergstraße",
        "plz": "74072",
        "hausnr": "41",
    },
}

ICON_MAP = {
    "R": "mdi:trash-can",
    "B": "mdi:leaf",
    "GRÜN": "mdi:leaf",
    "G": "mdi:recycle",
    "A": "mdi:package-variant",
    "BT": "mdi:package-variant",
}


class Source:
    def __init__(self, plz: int, strasse: str, hausnr: str | int):
        self._plz: str = str(plz)
        self._strasse: str = strasse
        self._hausnr: str = str(hausnr)
        self._ics = ICS()

    def fetch(self):
        r = requests.get(
            "https://abfallratgeber.heilbronn.de/excel_hn/htdocs/street.json"
        )
        r.raise_for_status()
        streets: dict = r.json()

        # all the data is spilt in to two files for different kinds of trash
        year_response = requests.get(
            "https://abfallratgeber.heilbronn.de/excel_hn/htdocs/yearObject.json"
        )
        year_response.raise_for_status()

        yearB_response = requests.get(
            "https://abfallratgeber.heilbronn.de/excel_hn/htdocs/yearBObject.json"
        )
        yearB_response.raise_for_status()

        days_list: list[dict] = [year_response.json(), yearB_response.json()]

        keys = []

        # get the values to search for in the json and save them in keys
        for street in streets:

            if (street["route"] == self._strasse) and (
                street["postal_code"] == self._plz
            ):

                if ("street_number" in street) and (
                    self._hausnr not in street["street_number"]
                ):
                    continue
                keys = []
                for key in list({street["area"], street["g"], street["bt"]}):
                    keys.append(key)
                    if "-" in key:
                        keys.append(key.split("-")[0])
                break

        if keys == []:
            raise Exception(
                "no address found for "
                + self._strasse
                + " "
                + self._hausnr
                + " "
                + self._plz
            )

        entries = []
        # iterate over both json files and search for the keys
        for days in days_list:
            for day in days.values():
                if "date" not in day:
                    continue

                date: dict = datetime.strptime(day["date"], "%d.%m.%Y").date()

                for key in keys:
                    if key in day["districts"] and day["districts"][key] != []:
                        for entry in day["districts"][key]:
                            if entry in ICON_MAP:
                                icon = ICON_MAP.get(entry)
                            elif len(entry) >= 2 and entry[:2] == "BT":
                                icon = ICON_MAP.get("BT")
                            else:
                                icon = ICON_MAP.get(entry[0])
                            entries.append(Collection(date, entry, icon))

        return entries
