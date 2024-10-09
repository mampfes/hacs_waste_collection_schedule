from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Ealing Council"
DESCRIPTION = "Source for Ealing Council."
URL = "https://www.ealing.gov.uk"
TEST_CASES = {
    "11 LOTHAIR ROAD, EALING, LONDON, W5 4TA": {"uprn": 12081500},
    "53 CREIGHTON ROAD, EALING, LONDON, W5 4SH": {"uprn": "12082293"},
}


ICON_MAP = {
    "BLACK": "mdi:trash-can",
    "GARDEN": "mdi:leaf",
    "BLUE": "mdi:recycle",
    "FOOD": "mdi:food-apple",
}


API_URL = "https://www.ealing.gov.uk/site/custom_scripts/WasteCollectionWS/home/FindCollection"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self) -> list[Collection]:
        args = {"UPRN": self._uprn}

        r = requests.post(API_URL, data=args)
        r.raise_for_status()

        data = r.json()

        entries = []
        for d in data["param2"]:
            bin_type = d["Service"]
            icon = ICON_MAP.get(bin_type.split()[0])  # Collection icon
            for date_str in d["collectionDate"]:
                date = datetime.strptime(date_str, "%d/%m/%Y").date()
                entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
