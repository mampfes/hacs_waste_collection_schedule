from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Lincolnshire Council"
DESCRIPTION = "Source for northlincs.gov.uk services for North Lincolnshire Council, UK."
URL = "https://www.northlincs.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100050200824"},
    "Test_002": {"uprn": "100050188326"},
    "Test_003": {"uprn": 100050199446},
    "Test_004": {"uprn": 100050196285},
}
ICON_MAP = {
    "Plastic and cardboard wheeled bin": "mdi:recycle",
    "Blue kerbside box - paper": "mdi:package-variant",
    "Brown garden waste wheeled bin": "mdi:leaf",
    "Textiles Bag": "mdi:sack",
    "Green kerbside box - cans, glass and aluminium foil": "mdi:glass-fragile",
    "General waste wheeled bin": "mdi:trash-can",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        r = requests.get(
            f"https://m.northlincs.gov.uk/collection_dates/{self._uprn}/0/6?_=1546855781728&format=json")
        r.raise_for_status()

        entries = []

        for collection in r.json()["Collections"]:
            date_string = collection["CollectionDate"].replace("/Date(", "").replace(")/", "")[:10]
            date = datetime.fromtimestamp(int(date_string)).date()
            waste_type = collection["BinCodeDescription"]
            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),

                )
            )
        return entries
