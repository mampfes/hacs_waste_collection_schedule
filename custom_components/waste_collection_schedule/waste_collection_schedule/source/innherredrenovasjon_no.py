import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Innherred Renovasjon"
DESCRIPTION = (
    "Source for innherredrenovasjon.no services for Innherred Renovasjon, Norway."
)
URL = "https://innherredrenovasjon.no/"

TEST_CASES = {
    "Test_001": {"address": "Geving%C3%A5sen 206"},
    "Test_002": {"address": "Bollgardssletta 211 A"},
    "Test_003": {"address": "Nordregata 2"},
}

API_URL = (
    "https://innherredrenovasjon.no/wp-json/ir/v1/garbage-disposal-dates-by-address"
)

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Bioavfall": "mdi:leaf",
    "Papp/papir": "mdi:package-variant",
    "Plastemballasje": "mdi:recycle",
    "Glass- og metallemballasje": "mdi:bottle-soda",
    "Matavfall": "mdi:trash-can",
    "Restavfall mini": "mdi:trash-can",
}

HEADERS = {"user-agent": "Mozilla/5.0"}


class Source:
    def __init__(self, address: str):
        self._address = str(address)

    def fetch(self):
        args = {"address": self._address}

        r = requests.get(API_URL, params=args, headers=HEADERS)
        r.raise_for_status()

        data = json.loads(r.content)

        entries = []

        for f in data.values():
            fraction_name = f["fraction_name"]
            for d in f["dates"]:
                entries.append(
                    Collection(
                        date=datetime.strptime(d, "%Y-%m-%dT%H:%M:%S").date(),
                        t=fraction_name,
                        icon=ICON_MAP.get(fraction_name),
                    )
                )

        return entries
