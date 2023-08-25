from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Rhondda Cynon Taf County Borough Council"
DESCRIPTION = "Source for rctcbc.gov.uk services for Rhondda Cynon Taf County Borough Council, Wales, UK"
URL = "rctcbc.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "10024274791"},
    "Test_002": {"uprn": "100100718352"},
    "Test_003": {"uprn": 100100733093},
}
ICON_MAP = {
    "BLACK BAGS": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "FOOD WASTE": "mdi:food",
    "GARDEN WASTE": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()
        # website appears to display ~4 months worth of collections, so iterate through those pages
        entries = []
        for month in range(0, 4):
            r = s.get(
                f"https://www.rctcbc.gov.uk/EN/Resident/RecyclingandWaste/RecyclingandWasteCollectionDays.aspx?uprn={self._uprn}&month={month}"
            )
            soup = BeautifulSoup(r.text, "html.parser")
            calendar_month = soup.find("div", {"class": "calendar-month"})
            calendar_day = soup.find_all(
                "div", {"class": "card-body card-body-padding"}
            )
            for day in calendar_day:
                pickups = day.find_all("a")
                if len(pickups) != 0:
                    d = day.find("div", {"class": "card-title"})
                    dt = d.text.strip() + " " + calendar_month.text.strip()
                    for pickup in pickups:
                        entries.append(
                            Collection(
                                date=datetime.strptime(
                                    dt,
                                    "%d %B %Y",
                                ).date(),
                                t=pickup.text,
                                icon=ICON_MAP.get(pickup.text.upper()),
                            )
                        )

        return entries
