import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaft Nürnberger Land"
DESCRIPTION = "Source for Nürnberger Land"
URL = "https://nuernberger-land.de"
TEST_CASES = {
    "Schwarzenbruck, Mühlbergstraße": {"id": 16952001},
    "Burgthann, Brunhildstr": {"id": 14398001},
    "Kirchensittenbach, Erlenweg": {"id": 15192001},
}

API_URL = "https://abfuhrkalender.nuernberger-land.de/waste_calendar"
FILTER = "rm:bio:p:dsd:poison"

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biotonne": "mdi:leaf",
    "Gelber Sack": "mdi:recycle",
    "Papier": "mdi:package-variant",
    "Giftmobil": "mdi:biohazard",
}


class Source:
    def __init__(self, id):
        self._id = id
        self._ics = ICS(split_at="/")

    def fetch(self):
        # fetch the ical
        r = requests.get(f"{API_URL}/ical?id={self._id}&filter={FILTER}")
        r.raise_for_status()

        # replace non-ascii character in UID, otherwise ICS converter will fail
        ics = ""
        for line in r.text.splitlines():
            if line.startswith("UID"):
                line = line.replace("ä", "ae")
                line = line.replace("ö", "oe")
                line = line.replace("ü", "ue")
            ics += line.strip()
            ics += "\n"

        dates = self._ics.convert(ics)

        entries = []

        for d in dates:
            entries.append(Collection(date=d[0], t=d[1], icon=ICON_MAP.get(d[1])))

        return entries
