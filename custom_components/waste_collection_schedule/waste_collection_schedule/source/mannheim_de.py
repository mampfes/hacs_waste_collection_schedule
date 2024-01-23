import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallkalender Mannheim"
DESCRIPTION = "Source für Abfallkalender Mannheim"
URL = "https://www.mannheim.de"

TEST_CASES = {
    "mannheim": {"f_id_location": 454016},  # Malzstr. 24
}

API_URL = "https://www.insert-it.de/BmsAbfallkalenderMannheim/Main/Calender"

BIN_MAP = {
    "Rest": {"icon": "mdi:trash-can", "name": "Restmüll"},
    "Wertstoff": {"icon": "mdi:recycle", "name": "Sack/Tonne gelb"},
    "Bio": {"icon": "mdi:leaf", "name": "Biomüll"},
    "Papier": {"icon": "mdi:package-variant", "name": "Altpapier"},
    "Grünschnitt": {"icon": "mdi:leaf", "name": "Grünschnitt"},
}


LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, f_id_location):
        self._location = f_id_location
        self._ics = ICS(regex=r"Leerung:\s+(.*)")

    def fetch(self):
        now = datetime.now()

        entries = self.fetch_year(now.year)
        if now.month == 12:
            entries += self.fetch_year(now.year + 1)
        return entries

    def fetch_year(self, year):
        s = requests.Session()
        params = {"bmsLocationId": self._location, "year": year}

        r = s.get(API_URL, params=params)
        r.raise_for_status()
        r.encoding = "utf-8"

        entries = []

        dates = self._ics.convert(r.text)
        for d in dates:
            entries.append(
                Collection(
                    date=d[0],
                    t=BIN_MAP[d[1]]["name"],
                    icon=BIN_MAP[d[1]]["icon"],
                )
            )

        return entries
