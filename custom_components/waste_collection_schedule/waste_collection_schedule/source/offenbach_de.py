import re
import requests
from datetime import datetime

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallkalender Offenbach am Main"
DESCRIPTION = "Source für Abfallkalender Offenbach"
URL = "https://www.offenbach.de/stadtwerke/stadtservice/Entsorgung/abfallkalender.php"
TEST_CASES = {
    "offenbach": {"f_id_location": 7036 }, # KaiserStraße 1
}

API_URL = "https://www.insert-it.de/BmsAbfallkalenderOffenbach/Main/Calender"
RE_FILTER_NAME = re.compile(r': (.*?)\s+\(')

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biomüll": "mdi:leaf",
    "DSD": "mdi:recycle",
    "Altpapier": "mdi:package-variant",
}

class Source:
    def __init__(self, f_id_location):
        self._location = f_id_location
        self._ics = ICS()

    def fetch(self):
        s = requests.Session()
        params = {
            "bmsLocationId": self._location,
            "year": datetime.now().year
        }

        r = s.get(API_URL, params=params)
        r.raise_for_status()

        entries = []

        dates = self._ics.convert(r.content.decode('utf-8'))
        for d in dates:
            m = RE_FILTER_NAME.search(d[1])
            mull_type = m.group(1) if m else d[1].replace("Leerung: ", "")
            entries.append(Collection(d[0], mull_type, icon=ICON_MAP.get(mull_type, "mdi:trash-can")))

        return entries