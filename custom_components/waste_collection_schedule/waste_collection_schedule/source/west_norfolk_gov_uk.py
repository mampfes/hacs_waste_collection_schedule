import re
import requests
from bs4 import BeautifulSoup

from datetime import datetime
from waste_collection_schedule import Collection


TITLE = "Borough Council of King's Lynn & West Norfolk"
DESCRIPTION = "Source for www.west-norfolk.gov.uk services for Borough Council of King's Lynn & West Norfolk, UK."
URL = "https://www.west-norfolk.gov.uk"
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
TEST_CASES = {
    "Test_001": {"uprn": "100090969937"},
    "Test_002": {"uprn": "100090989776"},
    "Test_003": {"uprn": "10000021270"},
    "Test_004": {"uprn": 100090969937},
}
ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf"
}

class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):

        # Get session and amend cookies
        s = requests.Session()
        r0 = s.get(
            "https://www.west-norfolk.gov.uk/info/20174/bins_and_recycling_collection_dates",
            headers=HEADERS
        )
        s.cookies.update(
            {
                "bcklwn_store": s.cookies.get("PHPSESSID"),
                "bcklwn_uprn": self._uprn,
            }
        )

        # Get initial collection dates using updated cookies
        r1= s.get(
            "https://www.west-norfolk.gov.uk/info/20174/bins_and_recycling_collection_dates",
            headers=HEADERS,
            cookies=s.cookies
        )

        # Get extended collection schedule from calendar end point
        r2 = s.get(
            "https://www.west-norfolk.gov.uk/bincollectionscalendar",
            headers=HEADERS,
            cookies=s.cookies
        )

        # Extract dates and waste types: Extracts ~6 months worth of collections from the optional website calendar page
        entries = []
        soup = BeautifulSoup(r2.text, "html.parser")
        pickups = soup.findAll("div", {"class": "cldr_month"})
        for item in pickups:
            month = item.find("h2")
            dates = item.findAll("td", {"class": re.compile(" (recycling|refuse|garden)")})
            for d in dates:
                attr = d.attrs.get("class")
                for a in attr[2:]:
                    dt = d.text + " " + month.text
                    entries.append(
                        Collection(
                            date = datetime.strptime(dt, "%d %B %Y").date(),
                            t = a,
                            icon = ICON_MAP.get(a.upper())
                        )
                    )

        return entries