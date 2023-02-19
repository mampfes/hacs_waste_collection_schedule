import requests
from bs4 import BeautifulSoup

from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Basingstoke and Deane Borough Council"
DESCRIPTION = "Source for basingstoke.gov.uk services for Basingstoke and Deane Borough Council, UK."
URL = "https://basingstoke.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100060234732"},
    "Test_002": {"uprn": "100060218986"},
    "Test_003": {"uprn": 100060235836},
    "Test_004": {"uprn": 100060224194},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "WASTE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
    "GLASS": "mdi:glass-fragile",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):  
        s = requests.Session()
        REQUEST_COOKIES = {
            "cookie_control_popup": "N",
            "WhenAreMyBinsCollected": self._uprn
        }
        r = requests.get(
            "https://www.basingstoke.gov.uk/bincollections", headers=HEADERS, cookies=REQUEST_COOKIES
        )

        soup = BeautifulSoup(r.text, "html.parser")

        services = soup.findAll("div", {"class": "service"})

        entries = []
    
        for service in services:
            waste_type = service.find("h2").text.split(" ")[0]
            schedule_dates = service.findAll("li")
            for schedule in schedule_dates:
                # dt.append(c.text)
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            schedule.text, "%A, %d %B %Y").date(),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type.upper()),
                    )
                )

        return entries

