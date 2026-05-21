import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

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
    "Plastic and cardboard wheeled bin": Icons.PLASTIC_PACKAGING,
    "Blue kerbside box - paper": Icons.PAPER,
    "Brown garden waste wheeled bin": Icons.GARDEN,
    "Textiles Bag": Icons.TEXTILE,
    "Green kerbside box - cans, glass and aluminium foil": Icons.GLASS,
    "General waste wheeled bin": Icons.GENERAL_WASTE,
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
