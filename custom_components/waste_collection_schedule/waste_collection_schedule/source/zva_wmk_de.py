import requests
import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

import urllib

TITLE = "Zweckverband Abfallwirtschaft Werra-Meißner-Kreis"
DESCRIPTION = "Source for Zweckverband Abfallwirtschaft Werra-Meißner-Kreis"
URL = "https://www.zva-wmk.de/"
TEST_CASES = {
    "Frankenhain": {"city": "Berkatal - Frankenhain", "street": "Teichhof"},
    "Hebenshausen": {"city": "Neu-Eichenberg - Hebenshausen", "street": "Bachstraße"},
    "Vockerode": {"city": "Meißner - Vockerode", "street": "Feuerwehr"}
}


class Source:
    def __init__(self, city, street):
        self._city = city
        self._street = street
        self._ics = ICS(split_at=" / ")

    def fetch(self):
        city = self._city.replace('ß', 'ẞ').upper()
        city = city.replace(" - ", "_")
        city = city.replace(" ", "+")
        city = city.replace("ẞ", "ß")
        street = self._street
        street = street.replace(" ","+")
        today = datetime.date.today()
        year = today.year
        year = 2023
        if year == 2022:
           yearstr = ""
           street = self._street.upper()
        else:
           yearstr = ("-" + str(year))
        payload = {"city": city, "street": street}
        
        urlzva = "https://www.zva-wmk.de/termine/schnellsuche"+yearstr+"&type=all&link=ical&timestart=6&fullday=1&timeend=17&reminder=1440&display=0"

        r = requests.get(urlzva, params=payload)
        
        r.encoding = r.apparent_encoding
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
           entries.append(Collection(d[0], d[1]))
        return entries
