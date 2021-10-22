from typing import Dict
import math
import time
import json
import datetime

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
import requests

TITLE = "Hygea"
DESCRIPTION = "Source for Hygea garbage collection"
URL = "https://www.hygea.be/"
TEST_CASES = {
    "Soignies": {
        "street_index": "3758",
    },
    "Frameries": {
        "street_index": "4203",
    },
    "Erquelinnes": {
        "street_index": "6560",
    },
}


class Source:
    def __init__(self, street_index):
        self.street_index = street_index

    def fetch(self):
        response = requests.get(f"https://www.hygea.be/displaycal.html?street={self.street_index}&start={math.trunc(time.time())}&end={math.trunc(time.time()) + 2678400}" )
        data = json.loads(response.text)
        entries = []

        for day in range(data):
            if "sacvert" in data["className"]:
                entries.append(
                    Collection(
                        datetime.datetime.strptime(day["start"], "%Y-%m-%dT%H:%M:%S%z"),
                        "Déchets Organiques"
                    )
                )
            if "pmc" in data["className"]:
                entries.append(
                    Collection(
                        datetime.datetime.strptime(day["start"], "%Y-%m-%dT%H:%M:%S%z"),
                        "PMC"
                    )
                )
            if "fourth" in data["className"]:
                entries.append(
                    Collection(
                        datetime.datetime.strptime(day["start"], "%Y-%m-%dT%H:%M:%S%z"),
                        "Papier & cartons"
                    )
                )
            if "contener" in data["className"]:
                entries.append(
                    Collection(
                        datetime.datetime.strptime(day["start"], "%Y-%m-%dT%H:%M:%S%z"),
                        "Déchets résiduels"
                    )
                )
        return entries
