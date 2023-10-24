import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Lincolnshire Council"
DESCRIPTION = (
    "Source for northlincs.gov.uk services for North Lincolnshire Council, UK."
)
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
            f"https://m.northlincs.gov.uk/bin_collections?no_collections=20&uprn={self._uprn}"
        )
        r.raise_for_status()
        r_json = json.loads(r.content.decode("utf-8-sig"))["Collections"]

        entries = []

        for collection in r_json:
            date = datetime.strptime(
                collection["CollectionDate"].split(" ")[0], "%Y-%m-%d"
            ).date()
            waste_type = collection["BinCodeDescription"]
            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )
        return entries
