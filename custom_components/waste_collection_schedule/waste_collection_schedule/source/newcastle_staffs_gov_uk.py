import logging
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection

TITLE = "Newcastle Under Lyme Borough Council"
DESCRIPTION = "Source for waste collection services for Newcastle Under Lyme Borough Council"
URL = "https://www.newcastle-staffs.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": 10013119164},
    "Test_002": {"uprn": "100061309206"},
    "Test_003": {"uprn": 100062119825},
    "Test_004": {"uprn": "100061343923"},
    "Test_005": {"uprn": 100062372553},
}
ICON_MAP = {
    "Household Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food Waste": "mdi:food",
    "Garden Waste": "mdi:leaf",
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}


_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn: str = None):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()
        r = s.get(f"https://webmap.newcastle-staffs.gov.uk/CollectionsDetailsWebFeed/CollectionDetails?uprn={self._uprn}", headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        rows = []
        for tr in soup.findAll("tr"):
            cells = []
            for cell in tr.findAll("td"):
                cells.append(cell)
            rows.append(cells)
        rows.pop(0)  # get rid of empty table header

        schedule = []  #[date, waste type]
        for row in rows:
            for cell in row:
                if row.index(cell) == 0:
                    dt = datetime.strptime(cell.text, "%A %d %B %Y").date()
                else:
                    bins = str(cell).replace("<td>", "").replace("</td>","").split("<br/>")
                    for bin in bins:
                        schedule.append([dt, bin])
                        if bin == "Household Rubbish":  # If subscribed to Garden Waste, it's collected alongside Household Waste
                            schedule.append([dt, "Garden Waste"])

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
