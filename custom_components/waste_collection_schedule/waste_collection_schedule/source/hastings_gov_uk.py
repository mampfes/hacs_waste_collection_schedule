from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Hastings Borough Council"
DESCRIPTION = "Source for hastings.gov.uk services for Hastings Borough Council, UK."
URL = "https://www.hastings.gov.uk/"
API_URL = "https://www.hastings.gov.uk/waste_recycling/lookup/"
HEADERS = {"user-agent": "Mozilla/5.0"}
TEST_CASES = {
    "Test_001": {"postcode": "TN34 1QF", "house_number": "36"},
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Rubbish": "mdi:trash-can",
}


class Source:
    def __init__(self, postcode: str, house_number: str | int):
        self._potcode = postcode
        self._house = str(house_number)

    def get_viewstate(self, content: str) -> dict:
        tags = {}
        soup = BeautifulSoup(content, "html.parser")
        hidden_tags = soup.findAll("input", type="hidden")
        for _, tag in enumerate(hidden_tags):
            tags[tag.get("name")] = tag.get("value")
        return tags

    def fetch(self):

        s = requests.Session()

        # perform address search to get viewstate info
        r = s.get(API_URL, headers=HEADERS)
        r.raise_for_status

        payload = self.get_viewstate(r.content)
        payload.update(
            {
                "ctl00$leftCol$postcode": self._potcode,
                "ctl00$leftCol$propertyNum": self._house,
                "ctl00$leftCol$ctl05": "Find Address",
            }
        )

        # get collection schedule
        r = s.post(API_URL, data=payload, headers=HEADERS)
        r.raise_for_status
        soup = BeautifulSoup(r.text, "html.parser")

        entries = []
        for _, waste in enumerate(ICON_MAP):
            container = soup.findAll("p", {"id": f"{waste}"})
            pickups = container[0].text.split("\r\n                ")
            for item in pickups[1:]:
                entries.append(
                    Collection(
                        date=datetime.strptime(item.strip(), "%A %d %B %Y").date(),
                        t=waste,
                        icon=ICON_MAP.get(waste),
                    )
                )

        return entries
