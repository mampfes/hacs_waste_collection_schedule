import json
import requests

from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Amber Valley Borough Council"
DESCRIPTION = "Source for ambervalley.gov.uk services for Amber Valley Borough Council, UK."
URL = "https://ambervalley.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100030011612"},
    "Test_002": {"uprn": "100030011654"},
    "test_003": {"uprn": 100030041980}
}

ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GREEN": "mdi:leaf",
    "COMMUNAL REFUSE": "mdi:trash-can",
    "COMMUNAL RECYCLING": "mdi:recycle",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        # get json file
        r = requests.get(
            f"https://info.ambervalley.gov.uk/WebServices/AVBCFeeds/WasteCollectionJSON.asmx/GetCollectionDetailsByUPRN?uprn={self._uprn}"
        )

        # extract data from json
        data = json.loads(r.text)
        wasteDict = {
            "REFUSE": data["refuseNextDate"],
            "RECYCLING": data["recyclingNextDate"],
            "GREEN": data["greenNextDate"],
            "COMMUNAL REFUSE": data["communalRefNextDate"],
            "COMMUNAL RECYCLING": data["communalRycNextDate"],
        }

        entries = []

        for item in wasteDict:
            if wasteDict[item] != "1900-01-01T00:00:00":
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            wasteDict[item], "%Y-%m-%dT%H:%M:%S").date(),
                        t=item,
                        icon=ICON_MAP.get(item),
                    )
                )

        return entries

