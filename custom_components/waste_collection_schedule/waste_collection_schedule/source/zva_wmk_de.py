import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaft Werra-Meißner-Kreis"
DESCRIPTION = "Source for Zweckverband Abfallwirtschaft Werra-Meißner-Kreis"
URL = "https://www.zva-wmk.de/"
TEST_CASES = {
    "Frankenhain": {"city": "Berkatal - Frankenhain", "street": "Teichhof"},
    "Hebenshausen": {"city": "Neu-Eichenberg - Hebenshausen", "street": "Bachstraße"},
    "Vockerode": {"city": "Meißner - Vockerode", "street": "Feuerwehr"},
}


class Source:
    def __init__(self, city, street):
        city = city.replace("ß", "ẞ").upper().replace("ẞ", "ß")
        city = city.replace(" - ", "_")
        self._city = city
        self._street = street
        self._ics = ICS(split_at=" / ")

    def fetch(self):
        today = datetime.date.today()

        entries = self._fetch_year(today.year)
        if today.month == 12:
            entries.extend(self._fetch_year(today.year + 1))

        return entries

    def _fetch_year(self, year):
        try:
            return self._fetch_yearstr(f"-{year}", self._street)
        except Exception:
            return self._fetch_yearstr("", self._street.upper())

    def _fetch_yearstr(self, yearstr, street):
        params = {"city": self._city, "street": street, "type": "all", "link": "ical"}

        r = requests.get(
            f"https://www.zva-wmk.de/termine/schnellsuche{yearstr}", params=params
        )
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
