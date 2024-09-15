import datetime
from waste_collection_schedule import Collection
import requests
from dateutil import parser
from bs4 import BeautifulSoup

TITLE = "Wyre Borough Council" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for wyre.gov.uk"  # Describe your source
URL = "https://www.wyre.gov.uk"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {
    "Test_001": {"uprn": "10094000847"},
}
ICON_MAP = {
    "Grey Bin": "mdi:trash-can",
    "Blue Bin": "mdi:recycle",
    "Red Bin": "mdi:recycle",
    "Green bin": "mdi:leaf",
}


API_URL = "https://www.wyre.gov.uk/bincollections"


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        response = requests.get(
            "https://www.wyre.gov.uk/bincollections", params={"uprn": self._uprn}
        )
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        bins = soup.find_all("h3", class_="bin-collection-tasks__heading")
        dates = soup.find_all("p", class_="bin-collection-tasks__date")
        for date_tag, bin_tag in zip(dates, bins):
            bint = " ".join(bin_tag.text.split()[2:4])
            date = parser.parse(date_tag.text).date()
        
            entries.append(
                Collection(
                    date=date,
                    t=bint,
                    icon=ICON_MAP.get(bint),
                )
            )

        return entries

