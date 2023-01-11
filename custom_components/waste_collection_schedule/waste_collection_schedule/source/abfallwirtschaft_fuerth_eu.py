import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaft Stadt Fürth"
DESCRIPTION = "Source for Stadt Fürth"
URL = "https://abfallwirtschaft.fuerth.eu/"
COUNTRY = "de"
TEST_CASES = {
    "Mühltalstrasse 4": {"id": 96983001},
    "Carlo-Schmid-Strasse 27": {"id": 96975001},    
}

API_URL = "https://abfallwirtschaft.fuerth.eu/termine.php"

ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Biotonne": "mdi:leaf",
    "Gelber Sack": "mdi:recycle",
    "Altpapier": "mdi:package-variant",
}


class Source:
    def __init__(self, id):
        self._id = id
        self._ics = ICS(split_at="/")

    def fetch(self):
        # fetch the ical
        r = requests.get(f"{API_URL}?icalexport={self._id}")
        r.raise_for_status()

        # replace non-ascii character in UID, otherwise ICS converter will fail
        ics = ""
        for line in r.text.splitlines():
            if line.startswith("UID"):
                line = line.replace("ä", "ae")
                line = line.replace("ö", "oe")
                line = line.replace("ü", "ue")
            ics += line
            ics += "\n"

        dates = self._ics.convert(ics)

        entries = []

        for d in dates:
            entries.append(Collection(date=d[0], t=d[1], icon=ICON_MAP.get(d[1])))
			
        return entries
