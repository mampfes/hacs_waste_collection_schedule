from datetime import datetime

import requests
from bs4 import BeautifulSoup

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Lanarkshire Council"
DESCRIPTION = "Source for waste collection services for North Lanarkshire Council"
URL = "https://northlanarkshire.gov.uk"
TEST_CASES = {
    "Test_001": {
        "uprn": "004510053797",
        "usrn": 000,
        },
    "Test_002": {
        "uprn": 4510053797,
        "usrn": 000,
        },
    "Test_003": {
        "uprn": 4510053797,
        "usrn": 000,
    },
}


ICON_MAP = {
    "DOMESTIC": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}


class Source:
    def __init__(self, uprn, usrn):
        self._uprn = str(uprn).zfill(12)
        self._usrn = str(usrn)


    def fetch(self):
        s = requests.Session()

        r = s.get(f"https://www.northlanarkshire.gov.uk/bin-collection-dates/{self._uprn}/{self._usrn}")
        r.raise_for_status

        soup = BeautifulSoup(r.text, "html.parser")



        entries = []
        res = requests.get(f"{API_URL}?uprn={self
            entries.append(
                Collection(
                    date=datetime.strptime(collection_date, "%d-%b-%Y").date(),
                    t=collection_type,
                    icon=ICON_MAP.get(collection_type.upper()),
                )
            )

        return entries
