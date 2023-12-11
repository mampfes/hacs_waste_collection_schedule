from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallkalender Offenbach am Main"
DESCRIPTION = "Source für Abfallkalender Offenbach"
URL = "https://www.offenbach.de"

TEST_CASES = {
    "offenbach": {"f_id_location": 7036},  # KaiserStraße 1
}

API_URL = "https://www.insert-it.de/BmsAbfallkalenderOffenbach/Main/Calender"

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biomüll": "mdi:leaf",
    "DSD": "mdi:recycle",
    "Altpapier": "mdi:package-variant",
}


class Source:
    def __init__(self, f_id_location):
        self._location = f_id_location
        self._ics = ICS(regex=r"Leerung:\s+(.*)\s+\(.*\)")

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
            entries.append(Collection(d[0], d[1], icon=ICON_MAP.get(d[1])))

        return entries
