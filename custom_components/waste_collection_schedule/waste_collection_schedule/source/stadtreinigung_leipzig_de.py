import json
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

_LOGGER = logging.getLogger(__name__)

TITLE = "Stadtreinigung Leipzig"
DESCRIPTION = "Source for Stadtreinigung Leipzig."
URL = "https://stadtreinigung-leipzig.de"
TEST_CASES = {"Bahnhofsallee": {"street": "Bahnhofsallee", "house_number": 7}}


class Source:
    def __init__(self, street, house_number):
        self._street = street
        self._house_number = house_number
        self._ics = ICS()

    def fetch(self):
        params = {
            "old_format": 1,
            "search": self._street,
        }

        # get list of streets and house numbers
        r = requests.get(
            "https://stadtreinigung-leipzig.de/rest/Navision/Streets", params=params
        )

        data = json.loads(r.text)
        if len(data["results"]) == 0:
            raise Exception(f"street not found: {self._street}")
        street_entry = data["results"].get(self._street)
        if street_entry is None:
            raise Exception(f"street not found: {self._street}")

        id = street_entry.get(str(self._house_number))
        if id is None:
            raise Exception(f"house_number not found: {self._house_number}")

        # get ics file
        params = {
            "position_nos": id,
            "name": f"{self._street} {self._house_number}",
            "mode": "download",
        }
        r = requests.get(
            "https://stadtreinigung-leipzig.de/wir-kommen-zu-ihnen/abfallkalender/ical.ics",
            params=params,
        )
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1].removesuffix(", ")))
        return entries
