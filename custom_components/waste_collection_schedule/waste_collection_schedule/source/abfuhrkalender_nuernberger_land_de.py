import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaft Nürnberger Land"
DESCRIPTION = "Source for Nürnberger Land"
URL = "https://abfuhrkalender.nuernberger-land.de"
TEST_CASES = {
    "Schwarzenbruck, Mühlbergstraße": {"id": 16952001},
    "Burgthann, Brunhildstr": {"id": 14398001},
    "Kirchensittenbach, Erlenweg": {"id": 15192001},
}

API_URL = "https://abfuhrkalender.nuernberger-land.de/waste_calendar"

ICON_MAP = {
    "Restmüll/Biotonne": "mdi:trash-can",
    "Biotonne" : "mdi:leaf",
    "Papier/gelber Sack" : "mdi:package-variant",
    "Giftmobil" : "mdi:biohazard",
}


class Source:
    def __init__(self, id):
        self._id = id
        self._ics = ICS()

    def fetch(self):

        # fetch a list of all city ids
        # fetch a list of all city districts
        # fetch a list of all streets
        # fetch a list of all street sections

        # fetch the ical

        r = requests.get(f"{API_URL}/ical?id={self._id}")
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = [
            Collection(date=entry[0], t=entry[1], icon=next(v for k, v in ICON_MAP.items() if k in entry[1]))
            for entry in dates
        ]

        return entries