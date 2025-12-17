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
    "Bad Sooden-Allendorf": {"city": "Bad Sooden-Allendorf - Allendorf", "street": "Kannhöhe"},
}

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
        "city": "Ort",
    }
}


class Source:
    def __init__(self, city, street):
        city = city.replace("Hessisch Lichtenau", "HESSISCH+LICHTENAU")
        city = city.replace("Bad Sooden", "BAD+SOODEN")
        city = city.replace("ß", "%C3%9F").upper()
        city = city.replace("Ä", "%C3%84")
        city = city.replace("Ü", "%C3%9C")
        city = city.replace("Ö", "%C3%96")
        city = city.replace(" - ", "_")
        street = street.replace("ß", "%C3%9F").upper()
        street = street.replace("Ä", "%C3%84")
        street = street.replace("Ü", "%C3%9C")
        street = street.replace("Ö", "%C3%96")
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
        match year:
                case 2021:
                        yearstr="schnellsuche-2021"
                case 2023:
                        yearstr="schnellsuche-2023"
                case 2024:
                        yearstr=""
                case 2025:
                        yearstr="schnellsuche-2020"
                case 2026:
                        yearstr="persönlicher-terminkalender-2026"                    
                case _:
                        yearstr="persönlicher-terminkalender-2026"
        try:
            return self._fetch_yearstr(yearstr, self._street)
        except Exception:
            return self._fetch_yearstr("", self._street.upper())

    def _fetch_yearstr(self, yearstr, street):
        params = {"city": self._city, "street": street, "type": "all", "link": "ical"}

        r = requests.get(
            f"https://www.zva-wmk.de/termine/{yearstr}", params=params
        )
        r.raise_for_status()

        dates = self._ics.convert(r.text)
        if not dates:
            raise ValueError("No entries found")

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
