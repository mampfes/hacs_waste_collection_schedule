import datetime
import urllib

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "ReMidt Orkland muni"
DESCRIPTION = "Source for Orkland muni."
URL = "https://www.remidt.no"
TEST_CASES = {
    "Follovegen": {"address": "Follovegen 1 B"},
    "Makrellsvingen": {"address": "Makrellsvingen 14 - 20"},
    "Taubaneveien": {"address": "Taubaneveien 46"},
    "Mistfjordveien": {"address": "Mistfjordveien 1299"},
}

API_URL = "https://kalender.renovasjonsportal.no/api/address/"  # or station"

ICON_MAP = {  # Optional: Dict of waste types and suitable mdi icons
    "Restavfall": "mdi:trash-can",
    "Glass og metallemballasje": "mdi:bottle-soda",
    "Matavfall": "mdi:leaf",
    "Papir": "mdi:package-variant",
    "Plastemballasje": "mdi:recycle",
}


class Source:
    def __init__(self, address: str):
        self.address = address

    def fetch(self):
        entries = []

        r = requests.get(API_URL + urllib.parse.quote(self.address))
        r.raise_for_status()
        address_id = r.json()["searchResults"][0]["id"]

        r = requests.get(API_URL + address_id + "/details/")
        r.raise_for_status()
        disposals = r.json()["disposals"]

        for disposal in disposals:
            entries.append(
                Collection(
                    date=datetime.datetime.fromisoformat(
                        disposal["date"]
                    ).date(),  # Collection date
                    t=disposal["fraction"],  # Collection type
                    icon=ICON_MAP.get(disposal["fraction"]),  # Collection icon
                )
            )

        return entries
