import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Landkreis Erlangen-Höchstadt"
DESCRIPTION = "Source for Landkreis Erlangen-Höchstadt"
URL = "https://www.erlangen-hoechstadt.de/"
TEST_CASES = {
    "Höchstadt": {"city": "Höchstadt", "street": "Böhmerwaldstraße"},
    "Brand": {"city": "Eckental", "street": "Eckenhaid, Amselweg"},
    "Ortsteile": {"city": "Wachenroth", "street": "Ort inkl. aller Ortsteile"},
}


class Source:
    def __init__(self, city, street):
        self._city = city
        self._street = street
        self._ics = ICS(split_at=" / ")

    def fetch(self):
        today = datetime.date.today()
        dates = self.fetch_year(today.year)
        if today.month == 12:
            dates.extend(self.fetch_year(today.year + 1))

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries

    def fetch_year(self, year):
        city = self._city.upper()
        street = self._street

        payload = {"ort": city, "strasse": street, "abfallart": "Alle", "jahr": year}
        r = requests.get(
            "https://www.erlangen-hoechstadt.de/komx/surface/dfxabfallics/GetAbfallIcs",
            params=payload,
        )
        r.raise_for_status()
        r.encoding = "utf-8"
        return self._ics.convert(r.text)
