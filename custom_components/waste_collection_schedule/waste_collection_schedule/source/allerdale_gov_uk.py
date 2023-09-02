import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Allerdale Borough Council"
DESCRIPTION = "Source for www.allerdale.gov.uk services for Allerdale Borough Council."
URL = "https://www.allerdale.gov.uk"
TEST_CASES = {
    "Keswick": {
        "address_postcode": "CA12 4HU",
        "address_name_number": "11",
    },
    "Workington": {
        "address_postcode": "CA14 3NS",
        "address_name_number": "177",
    },
    "Wigton": {
        "address_postcode": "CA7 9RS",
        "address_name_number": "55",
    },
}
ICON_MAP = {
    "Domestic Waste": "mdi:trash-can",
    "Glass Cans and Plastic Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}
API_URL = "https://abc-wrp.whitespacews.com/"

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self,
        address_name_number=None,
        address_postcode=None,
    ):
        self._address_name_number = address_name_number
        self._address_postcode = address_postcode

    def fetch(self):
        session = requests.Session()

        # get link from first page as has some kind of unique hash
        r = session.get(
            API_URL,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        alink = soup.find("a", text="View My Collections")

        if alink is None:
            raise Exception("Initial page did not load correctly")

        # replace 'seq' query string to skip next step
        nextpageurl = alink["href"].replace("seq=1", "seq=2")

        data = {
            "address_name_number": self._address_name_number,
            "address_postcode": self._address_postcode,
        }

        # get list of addresses
        r = session.post(nextpageurl, data)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")

        # get first address (if you don't enter enough argument values this won't find the right address)
        alink = soup.find("div", id="property_list").find("a")

        if alink is None:
            raise Exception("Address not found")

        nextpageurl = API_URL + alink["href"]

        # get collection page
        r = session.get(
            nextpageurl,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        if soup.find("span", id="waste-hint"):
            raise Exception("No scheduled services at this address")

        u1s = soup.find("section", id="scheduled-collections").find_all("u1")

        entries = []

        for u1 in u1s:
            lis = u1.find_all("li", recursive=False)
            entries.append(
                Collection(
                    date=datetime.strptime(
                        lis[1].text.replace("\n", ""), "%d/%m/%Y"
                    ).date(),
                    t=lis[2].text.replace("\n", ""),
                    icon=ICON_MAP.get(
                        lis[2]
                        .text.replace("\n", "")
                        .replace(" Collection", "")
                        .replace(" Service", "")
                    ),
                )
            )

        return entries
