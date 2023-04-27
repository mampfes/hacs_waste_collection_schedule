import requests
import json

from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Bedford Borough Council"
DESCRIPTION = "Source for bradford.gov.uk services for Bedford Borough Council, UK."
URL = "https://bedford.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100080009302"},
    "Test_002": {"uprn": "100081207036"},
    "Test_003": {"uprn": 100080018481},
    "Test_004": {"uprn": 100080023672},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "BLACK BIN": "mdi:trash-can",
    "ORANGE BIN": "mdi:recycle",
    "GREEN BIN": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):

        s = requests.Session()
        r = s.get(f"https://bbaz-as-prod-bartecapi.azurewebsites.net/api/bincollections/residential/getbyuprn/{self._uprn}/35", headers=HEADERS)
        json_data = json.loads(r.text)["BinCollections"]

        entries = []

        for day in json_data:
            for bin in day:
                entries.append(
                    Collection(
                        date=datetime.strptime(bin["JobScheduledStart"], "%Y-%m-%dT00:00:00").date(),
                        t=bin["BinType"],
                        icon=ICON_MAP.get(bin["BinType"].upper()),
                    )
                )

        return entries
