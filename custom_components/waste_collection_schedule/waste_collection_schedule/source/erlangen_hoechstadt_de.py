import requests
import datetime
from waste_collection_schedule import Collection # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

import urllib

TITLE = "Landkreis Erlangen-Höchstadt"
DESCRIPTION = "Source for Landkreis Erlangen-Höchstadt"
URL = "https://www.erlangen-hoechstadt.de/"
TEST_CASES = {
    "Höchstadt": {"city": "Höchstadt", "street": "Böhmerwaldstraße"},
    "Brand": {"city": "Eckental", "street": "Eckenhaid, Amselweg"}
}


class Source:
    def __init__(self, city, street):
        self._city = city
        self._street = street
        self._ics = ICS()

    def fetch(self):
        city = urllib.parse.quote(self._city.upper())
        street = urllib.parse.quote(self._street)
        today = datetime.date.today()
        year = today.year
        r = requests.get(
            f"https://www.erlangen-hoechstadt.de/komx/surface/dfxabfallics/GetAbfallIcs?ort={city}&strasse={street}&abfallart=Alle&jahr={year}"
        )
        r.encoding = r.apparent_encoding
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
