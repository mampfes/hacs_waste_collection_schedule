import logging
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Newcastle Under Lyme Borough Council"
DESCRIPTION = (
    "Source for waste collection services for Newcastle Under Lyme Borough Council"
)
URL = "https://www.newcastle-staffs.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": 100031744129},
    "Test_002": {"uprn": "100031726082"},
    "Test_003": {"uprn": 100031736973},
    "Test_004": {"uprn": "200004602766"},
}
ICON_MAP = {
    "Household Rubbish": "mdi:trash-can",
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
        today = datetime.now().date()
        year = today.year

        s = requests.Session()
        r = s.get(
            f"https://www.newcastle-staffs.gov.uk/homepage/97/check-your-bin-day?uprn={self._uprn}",
            headers=HEADERS,
        )
        soup = BeautifulSoup(r.text, "html.parser")

        rows = []
        for tr in soup.findAll("tr"):
            cells = []
            for cell in tr.findAll("td"):
                cells.append(cell)
            rows.append(cells)
        rows.pop(0)  # get rid of empty table header

        schedule = []  # [date, waste type]
        for row in rows:
            for cell in row:
                if row.index(cell) == 0:
                    # Source doesn't include the year, so assume all dates are for the current year
                    dt = datetime.strptime(cell.text + str(year), "%A %d %B%Y").date()
                    # If date in more than 4 weeks in the past, assume it's near the year end and increment to next year
                    if (dt - today) < timedelta(days=-31):
                        dt = dt.replace(year=dt.year + 1)
                else:
                    bins = (
                        str(cell)
                        .replace("\n", "")
                        .replace("<td>", "")
                        .replace("</td>", "")
                        .split("<br/>")
                    )
                    for bin in bins[:-1]:
                        schedule.append([dt, bin.strip()])

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
