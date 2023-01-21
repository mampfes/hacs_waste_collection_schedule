from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Central Bedfordshire Council"
DESCRIPTION = (
    "Source for www.centralbedfordshire.gov.uk services for Central Bedfordshire"
)
URL = "https://www.centralbedfordshire.gov.uk"
TEST_CASES = {
    "postcode has space": {"postcode": "SG15 6YF", "house_name": "10 Old School Walk"},
    "postcode without space": {
        "postcode": "SG180LL",
        "house_name": "1 Chestnut Avenue",
    },
}

ICON_MAP = {
    "Refuse (black bin)": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden waste": "mdi:leaf",
    "Food waste": "mdi:food-apple",
}


class Source:
    def __init__(self, postcode, house_name):
        self._postcode = postcode
        self._house_name = house_name

    def fetch(self):
        session = requests.Session()

        # Lookup postcode, the use house name to get UPRN
        data = {
            "postcode": self._postcode,
        }
        r = session.post(
            "https://www.centralbedfordshire.gov.uk/info/163/bins_and_waste_collections_-_check_bin_collection_days",
            data=data,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")
        address = soup.find("select", id="address").find(
            "option", text=lambda value: value and value.startswith(self._house_name)
        )

        if address is None:
            raise Exception("address not found")
        self._uprn = address["value"]

        data = {
            "address_text": address.text,
            "address": self._uprn,
            "postcode": self._postcode,
        }
        r = session.post(
            "https://www.centralbedfordshire.gov.uk/info/163/bins_and_waste_collections_-_check_bin_collection_days",
            data=data,
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        s = soup.find("div", id="collections").find_all("h3")

        entries = []

        for collection in s:
            date = datetime.strptime(collection.text, "%A, %d %B %Y").date()

            for sibling in collection.next_siblings:
                if (
                    sibling.name == "h3"
                    or sibling.name == "p"
                    or sibling.name == "a"
                    or sibling.name == "div"
                ):
                    break
                if sibling.name != "br":
                    entries.append(
                        Collection(
                            date=date,
                            t=sibling.text,
                            icon=ICON_MAP.get(sibling.text),
                        )
                    )

        return entries
