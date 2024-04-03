from datetime import datetime, timedelta
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "BCP Council"
DESCRIPTION = "Source for Bournemouth, Chirstchurch and Poole  Council, UK."
URL = "https://www.bcpcouncil.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": 10013449141},
    "Test_002": {"uprn": "10001085438"},
    "Test_003": {"uprn": "100040567667"}
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Rubbish": "mdi:trash-can",
    "Garden Waste": "mdi:leaf",
    "Food Waste": "mdi:food",
}
API_URL = "https://online.bcpcouncil.gov.uk/bcp-apis?api=BinDayLookup&uprn={uprn}"

class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn)

    def fetch(self):
        r = requests.get(API_URL.format(uprn=self._uprn))
        json_data = json.loads(r.content)

        entries = []

        for bin in json_data:
            bin_type = bin["BinType"]
            next_date = (datetime.strptime(bin["Next"], "%m/%d/%Y %I:%M:%S %p") + timedelta(hours=1)).date()
            subsequent_date = (datetime.strptime(bin["Subsequent"], "%m/%d/%Y %I:%M:%S %p") + timedelta(hours=1)).date()
            entries.append(
                Collection(
                    date=next_date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )
            entries.append(
                Collection(
                    date=subsequent_date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        return entries
