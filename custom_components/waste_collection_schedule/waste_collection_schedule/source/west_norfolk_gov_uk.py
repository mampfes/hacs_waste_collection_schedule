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
    # "Test_002": {"uprn": "100080977050"},
    # "Test_003": {"uprn": "100090969937"},
    "Test_004": {"uprn": 100090969937},
}

ICON_MAP = {
    "food": "mdi:apple",
    "garden": "mdi:tree",
    "refuse": "mdi:trash-can",
    "recycling": "mdi:recycle"
}

class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):

        # get session id and amend cookies
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

        # get collection dates using updated cookies
        r1= s.get(
            "https://www.west-norfolk.gov.uk/info/20174/bins_and_recycling_collection_dates",
            headers=HEADERS,
            cookies=s.cookies
        )

        # extract dates and waste types
        entries = []
        soup = BeautifulSoup(r1.text, "html.parser")
        pickups = soup.findAll("div", {"class": "bin_date_container"})
        for item in pickups:
            dt = item.find("h3", {"class": "collectiondate"})
            waste = item.findAll("img")
            for w in waste:
                entries.append(
                Collection(
                    # date= datetime.strptime(str(dt.text), "%A %d %B %Y"),
                    t=w["alt"],
                    icon=ICON_MAP.get(w["alt"])
                )
            )

        return entries