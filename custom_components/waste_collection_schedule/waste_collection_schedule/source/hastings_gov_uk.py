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
    "Test_001": {"postcode": "TN34 1QF", "house_number": 36, "uprn": 100060038877},
    "Test_002": {"postcode": "TN34 2DL", "house_number": "28A", "uprn": "10070609836"},
    "Test_003": {"postcode": "TN37 7QH", "house_number": 5, "uprn": "100060041770"},
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Rubbish": "mdi:trash-can",
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "n easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details",
}
PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details",
    }
}


class Source:
    def __init__(self, postcode: str, house_number: str | int, uprn: str | int):
        self._postcode = str(postcode)
        self._house = str(house_number)
        self._uprn = str(uprn)

    def get_viewstate(self, content: str) -> dict:
        tags = {}
        soup = BeautifulSoup(content, "html.parser")
        hidden_tags = soup.findAll("input", type="hidden")
        for _, tag in enumerate(hidden_tags):
            tags[tag.get("name")] = tag.get("value")
        return tags

    def fetch(self):
        s = requests.Session()

        # visit webpage to get viewstate info
        r = s.get(API_URL, headers=HEADERS)
        r.raise_for_status

        # update payload and perform search
        payload = self.get_viewstate(r.content)
        payload.update(
            {
                "ctl00$leftCol$postcode": self._postcode,
                "ctl00$leftCol$propertyNum": self._house,
                "ctl00$leftCol$ctl05": "Find Address",
            }
        )
        r = s.post(API_URL, data=payload, headers=HEADERS)
        r.raise_for_status

        # if more than 1 match is returned, additional search using uprn is required
        if "ctl00_leftCol_AddressList" in r.text:
            payload = self.get_viewstate(r.content)
            payload.update(
                {
                    "ctl00$leftCol$addresses": self._uprn,
                    "ctl00$leftCol$ctl07": "Find Collection",
                }
            )
            r = s.post(API_URL, data=payload, headers=HEADERS)
            r.raise_for_status

        soup = BeautifulSoup(r.text, "html.parser")

        entries = []
        for waste in ICON_MAP:
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
