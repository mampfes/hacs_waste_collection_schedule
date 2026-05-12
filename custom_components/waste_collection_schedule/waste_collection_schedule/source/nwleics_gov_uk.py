from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North West Leicestershire District Council"  # Title will show up in README.md and info.md
DESCRIPTION = "Source for www.nwleics.gov.uk services for the city of North West Leicestershire District Council, UK"  # Describe your source
URL = "https://nwleics.gov.uk/"  # Insert url to service homepage. URL will show up in README.md and info.md
COUNTRY = "uk"
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Dunmore": {"uprn": "10002359002"},
    "Station Road": {"uprn": 100030573554},
}

RELATIVE_DATE_MAP = {
    "today": lambda: date.today(),
    "tomorrow": lambda: date.today() + timedelta(days=1),
}

API_URL = "https://my.nwleics.gov.uk/location?put=nwl{uprn}&rememberme=0&redirect=%2F"


ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Garden Waste": "mdi:leaf",
    "Yellow Bag": "mdi:recycle",
    "Blue Bag": "mdi:recycle",
    "Red Box": "mdi:recycle",
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        r = requests.get(API_URL.format(uprn=self._uprn))
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        refuse = soup.find("ul", {"class": "refuse"})
        li_items = refuse.find_all("li")

        entries = []

        for li in li_items:
            strong_tag = li.find("strong")
            a_tag = li.find("a")

            date_str = strong_tag.contents[0].strip()
            date_str_lower = date_str.lower()
            if date_str_lower in RELATIVE_DATE_MAP:
                collection_date = RELATIVE_DATE_MAP[date_str_lower]()
            else:
                collection_date = parser.parse(date_str).date()
            bin_type = a_tag.contents[0]

            entries.append(
                Collection(
                    date=collection_date,  # Collection date
                    t=bin_type,  # Collection type
                    icon=ICON_MAP.get(bin_type),  # Collection icon
                )
            )

        return entries
