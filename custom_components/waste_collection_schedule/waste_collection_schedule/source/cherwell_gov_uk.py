import re
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from waste_collection_schedule import Collection

TITLE = "Cherwell District Council"
DESCRIPTION = "Cherwell District Council North Oxfordshire, UK"
URL = "https://www.cherwell.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100120758315"},
    "Test_002": {"uprn": "100120780449"},
    "Test_003": {"uprn": 100120777153},
    "Test_004": {"uprn": 10011931488},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
REGEX = {
    "DATES": r"([Green|Blue|Brown]+ Bin)",
    "ORDINALS": r"(st|nd|rd|th) ",
}
ICON_MAP = {
    "GREEN BIN": "mdi:trash-can",
    "BLUE BIN": "mdi:recycle",
    "BROWN BIN": "mdi:leaf"
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)


    def fetch(self):
 
        today = datetime.now()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        yr = int(today.year)

        s = requests.Session()
        r = s.get(f"https://www.cherwell.gov.uk/homepage/129/?uprn={self._uprn}",headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        boxes = soup.findAll("div", {"class": "boxed"})

        entries = []
        for box in boxes:
            title = box.find("h3", {"class": "bin-collection-tasks__heading"}).text.replace("Your next ", "").replace(" collection", "")
            # Get date, append year, and increment year if date is >1 month in the past.
            # This tries to deal year-end dates when the YEAR is missing
            date = box.find("p", {"class": "bin-collection-tasks__date"}).text.strip()
            date = re.sub(REGEX["ORDINALS"],"", date)
            date += " " + str(yr)
            dt = datetime.strptime(date, "%d%B %Y")
            if (dt - today) < timedelta(days=-31):
                dt = dt.replace(year = dt.year + 1)

            entries.append(
                Collection(
                    date=dt.date(),
                    t=title,
                    icon=ICON_MAP.get(title.upper()),
            )
        )

        return entries
