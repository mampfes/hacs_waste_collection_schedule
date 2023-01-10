import urllib

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfalltermine Forchheim"
DESCRIPTION = "Source for Landkreis Forchheim"
URL = "https://www.abfalltermine-forchheim.de/"
TEST_CASES = {
    "Dormitz": {"city": "Dormitz", "area": "Dormitz"},
    "Rüsselbach": {"city": "Igensdorf", "area": "Oberrüsselbach"},
    "Kellerstraße": {
        "city": "Forchheim",
        "area": "Untere Kellerstraße (ab Adenauerallee bis Piastenbrücke)",
    },
}


class Source:
    def __init__(self, city, area):
        self._city = city
        self._area = area
        self._ics = ICS()

    def fetch(self):
        place = urllib.parse.quote(self._city + " - " + self._area)
        r = requests.get(
            f"http://www.abfalltermine-forchheim.de/Forchheim/Landkreis/{place}/ics?RESTMUELL=true&RESTMUELL_SINGLE=true&BIO=true&YELLOW_SACK=true&PAPER=true"
        )
        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
