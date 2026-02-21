from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Kesteven District Council"
DESCRIPTION = (
    "Source for n-kesteven.org.uk services for North Kesteven District Council, UK."
)
URL = "https://n-kesteven.org.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100030860713"},
    "Test_002": {"uprn": "10006514327"},
    "Test_003": {"uprn": "100030857039"},
    "Test_004": {"uprn": 100030864449},
    "Test_005": {"uprn": 10006507163},
}
ICON_MAP = {
    "BLACK": "mdi:trash-can",
    "GREEN": "mdi:recycle",
    "PURPLE": "mdi:newspaper",
    "BROWN": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()
        r = s.get(f"https://www.n-kesteven.org.uk/bins/display?uprn={self._uprn}")
        soup = BeautifulSoup(r.text, "html.parser")
        bin_type = soup.find_all("span", {"class": "font-weight-bold"})
        bin_dates = soup.find_all("strong")

        entries = []
        for idx in range(0, len(bin_type)):
            entries.append(
                Collection(
                    date=datetime.strptime(
                        bin_dates[idx].text.split(", ")[1], "%d %B %Y"
                    ).date(),
                    t=bin_type[idx].text.upper(),
                    icon=ICON_MAP.get(bin_type[idx].text.upper()),
                )
            )

        return entries
