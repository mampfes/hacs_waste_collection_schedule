import datetime
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Telšių keliai"
DESCRIPTION = "Source script for UAB 'Telšių keliai'"
URL = "https://tkeliai.lt/"
TEST_CASES = {
    "TestName1": {"location": "Butkų Juzės(1-31) g."},
    "TestName2": {"location": "Paragai k."},
    "TestName3": {"location": "Žalioji g."},
}

API_URL = "https://tkeliai.lt/ajax.php"
ICON_MAP = {
    "Mišrios komunalinės atliekos": "mdi:trash-can",
    "Kitos pakuočių atliekos": "mdi:recycle",
    "Stiklo pakuočių atliekos": "mdi:glass-fragile",
}


class Source:
    def __init__(self, location):
        self.location = location

    def fetch(self):
        data = {
            "action": "getDataAll",
            "module": "Atliekos",
            "lang": "lt",
            "location": self.location,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "",
        }

        response = requests.post(API_URL, headers=headers, data=data)

        data = json.loads(response.text)

        entries = []

        for collection in data["return"]:
            for date in collection["dates"].keys():
                entries.append(
                    Collection(
                        date=datetime.datetime.strptime(date, "%Y-%m-%d").date(),
                        t=collection["title"],
                        icon=ICON_MAP.get(collection["title"]),
                    )
                )

        return entries
