from datetime import datetime

import requests
import urllib3
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# With verify=True the POST fails due to a SSLCertVerificationError.
# Using verify=False works, but is not ideal. The following links may provide a better way of dealing with this:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
# These two lines areused to suppress the InsecureRequestWarning when using verify=False
urllib3.disable_warnings()

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
        REQUEST_COOKIES = {
            "cookie_control_popup": "N",
            "WhenAreMyBinsCollected": self._uprn,
        }
        r = requests.get(
            "https://www.basingstoke.gov.uk/bincollections",
            headers=HEADERS,
            cookies=REQUEST_COOKIES,
            verify=False,
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        services = soup.findAll("div", {"class": "service"})

        entries = []

        for service in services:
            waste_type = service.find("h2").text.split(" ")[0]
            schedule_dates = service.findAll("li")
            for schedule in schedule_dates:
                date_str = schedule.text.split("(")[0].strip()
                entries.append(
                    Collection(
                        date=datetime.strptime(date_str, "%A, %d %B %Y").date(),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type.upper()),
                    )
                )

        return entries
