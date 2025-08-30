import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "South Gloucestershire Council"  # Title will show up in README.md and info.md
DESCRIPTION = "Source script for southglos.gov.uk"  # Describe your source
URL = "https://southglos.gov.uk"  # Insert url to service homepage. URL will show up in README.md and info.md
HEADERS = {"user-agent": "Mozilla/5.0"}
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Test_001": {"uprn": "643346"},
    "Test_002": {"uprn": "641084"},
}
ICON_MAP = {  # Optional: Dict of waste types and suitable mdi icons
    "BLACK BIN": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN WASTE": "mdi:leaf",
    "FOOD BIN": "mdi:food",
}
WASTE_MAP = {  # map new collection names to old collection names for compatibility
    "Refuse": "BLACK BIN",
    "Recycling": "RECYCLING",
    "Garden": "GARDEN WASTE",
    "Food": "FOOD BIN",
}


class Source:
    def __init__(
        self, uprn: str
    ):  # argX correspond to the args dict in the source configuration
        self._uprn = uprn

    def fetch(self):
        session = requests.Session()
        r = session.get(
            f"https://api.southglos.gov.uk/wastecomp/GetCollectionDetails?uprn={self._uprn}",
            headers=HEADERS,
        )
        r.raise_for_status()
        pickups = r.json()

        entries = []
        for item in pickups["value"]:
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(
                        item["hso_nextcollection"].split("T")[0], "%Y-%m-%d"
                    ).date(),
                    t=WASTE_MAP[item["hso_servicename"]],
                    icon=ICON_MAP.get(WASTE_MAP[item["hso_servicename"]]),
                )
            )

        return entries
