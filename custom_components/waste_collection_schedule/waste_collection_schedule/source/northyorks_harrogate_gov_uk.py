import logging

import dateutil.parser as dparser
import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Yorkshire Council - Harrogate"
DESCRIPTION = "Source for North Yorkshire Council - Harrogate."

URL = "https://secure.harrogate.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": 100050389710},
    "Test_002": {"uprn": "100050389725"},
    "Test_003": {"uprn": 100050394291},
    "Test_004": {"uprn": "10003019065"},
}
ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food Waste": "mdi:food",
    "Garden Waste": "mdi:leaf",
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()
        r = s.get(
            f"https://secure.harrogate.gov.uk/inmyarea/property/?uprn={self._uprn}",
            headers=HEADERS,
        )
        soup = BeautifulSoup(r.text, "html.parser")

        schedule = []

        tableClass = soup.findAll("table", {"class": "hbcRounds"})
        for tr in tableClass[1].find_all("tr"):
            cells = []
            cells.append(dparser.parse(tr.find("td").text.lstrip(), fuzzy=True).date())
            cells.append(tr.find("th").text)
            schedule.append(cells)

        entries = []
        for pickup in schedule:
            entries.append(
                Collection(
                    date=pickup[0],
                    t=pickup[1],
                    icon=ICON_MAP.get(pickup[1]),
                )
            )

        return entries
