import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Hamilton City Council"
DESCRIPTION = "Source script for Hamilton City Council"
URL = "https://www.fightthelandfill.co.nz/"
TEST_CASES = {
    "1 Hamilton Parade": {"address": "1 Hamilton Parade"},
    "221b fox Street": {"address": "221b fox Street"},
}

API_URL = "https://api.hcc.govt.nz/FightTheLandFill/get_Collection_Dates"
ICON_MAP = {"Rubbish": "mdi:trash-can", "Recycling": "mdi:recycle"}


class Source:
    def __init__(self, address):
        self.address = address

    def fetch(self):
        r = requests.get(
            API_URL,
            params={"address_string": self.address},
        )
        json = r.json()

        # Extract entries from RedBin/YellowBin fields
        entries = [
            Collection(
                date=datetime.datetime.strptime(
                    json[0]["RedBin"], "%Y-%m-%dT%H:%M:%S"
                ).date(),
                t="Rubbish",
                icon=ICON_MAP.get("Rubbish"),
            ),
            Collection(
                date=datetime.datetime.strptime(
                    json[0]["YellowBin"], "%Y-%m-%dT%H:%M:%S"
                ).date(),
                t="Recycling",
                icon=ICON_MAP.get("Recycling"),
            ),
        ]

        return entries
