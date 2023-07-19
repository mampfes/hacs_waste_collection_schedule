import json
import re
from datetime import date
from time import strptime
from typing import List
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup as soup
from waste_collection_schedule import Collection

TITLE = "Broadland District Council"
DESCRIPTION = "Source for southnorfolkandbroadland.gov.uk services for South Norfolk and Broadland, UK"
URL = "https://area.southnorfolkandbroadland.gov.uk/"
EXTRA_INFO = [
    {
        "title": "South Norfolk Council",
        "url": "https://southnorfolkandbroadland.gov.uk/",
    },
]
TEST_CASES = {
    "Random address": {
        "address_payload": {
            "Uprn": "010014355477",
            "Address": "29 Mallard Way, Sprowston, Norwich, Norfolk, NR7 8DN",
            "X": "626227.00000",
            "Y": "312136.00000",
            "Ward": "Sprowston East",
            "Parish": "Sprowston",
            "Village": "Sprowston",
            "Street": "Mallard Way",
            "Authority": "2610",
        }
    },
    "Random address new Method": {
        "postcode": "NR7 8DN",
        "address": "29 Mallard Way, Sprowston, Norfolk, NR7 8DN",
    },
    "Big Tesco": {
        "address_payload": {
            "Uprn": "100091575309",
            "Address": "Tesco Stores Ltd, Blue Boar Lane, Sprowston, Norwich, Norfolk, NR7 8AB",
            "X": "625657.00000",
            "Y": "312146.00000",
            "Ward": "Sprowston East",
            "Parish": "Sprowston",
            "Village": "Sprowston",
            "Street": "Blue Boar Lane",
            "Authority": "2610",
        }
    },
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden (if applicable)": "mdi:leaf",
}

matcher = re.compile(r"^([A-Z][a-z]+) (\d{1,2}) ([A-Z][a-z]+) (\d{4})$")


def parse_date(date_str: str) -> date:
    match = matcher.match(date_str)
    if match is None:
        raise ValueError(f"Unable to parse date {date_str}")

    return date(
        int(match.group(4)),
        strptime(match.group(3)[:3], "%b").tm_mon,
        int(match.group(2)),
    )


def comparable(data: str) -> str:
    return data.replace(",", "").replace(" ", "").lower()


class Source:
    _address_payload: dict | None

    def __init__(
        self,
        address_payload: dict | None = None,
        postcode: str | None = None,
        address: str | None = None,
    ):
        self._address_payload = address_payload
        self._postcode = comparable(postcode) if postcode else None
        self._address = address if address else None

    def fetch(self) -> List[Collection]:
        if self._address_payload:
            return self.__fetch_by_payload()
        return self.__fetch_by_postcode_and_address()

    def __fetch_by_postcode_and_address(self) -> List[Collection]:
        if not self._postcode or not self._address:
            raise ValueError(
                "Either (address_payload) or (postcode and address) must be provided"
            )

        session = requests.Session()
        r = session.get(URL + "FindAddress")
        r.raise_for_status()
        page = soup(r.text, "html.parser")

        args = {
            "Postcode": self._postcode,
            "__RequestVerificationToken": page.find(
                "input", {"name": "__RequestVerificationToken"}
            )["value"],
        }
        r = session.post(URL + "FindAddress", data=args)
        r.raise_for_status()
        page = soup(r.text, "html.parser")
        addresses = page.find("select", {"id": "UprnAddress"}).find_all("option")

        if not addresses:
            raise ValueError(f"no addresses found for postcode {self._postcode}")

        args["__RequestVerificationToken"] = page.find(
            "input", {"name": "__RequestVerificationToken"}
        )["value"]

        found = False
        compare_address = self._address.replace(",", "").replace(" ", "").lower()

        for address in addresses:
            address_text = comparable(address.text)

            if (
                address_text == compare_address
                or address_text == compare_address.replace(self._postcode, "")
            ):
                args["UprnAddress"] = address["value"]
                found = True
                break

        if not found:
            raise ValueError(f"Address {self._address} not found")

        r = session.post(URL + "FindAddress/Submit", data=args)
        r.raise_for_status()
        return self.__get_data(r)

    def __fetch_by_payload(self) -> List[Collection]:
        r = requests.get(
            URL,
            headers={
                "Cookie": f"MyArea.Data={quote(json.dumps(self._address_payload))}"
            },
        )
        r.raise_for_status()
        return self.__get_data(r)

    def __get_data(self, r: requests.Response) -> List[Collection]:

        page = soup(r.text, "html.parser")
        bins_card = page.find("h3", text="Bins").parent
        bin_categories = bins_card.find_all("div", {"class": "card-text"})
        return [
            Collection(
                parse_date(tuple(bin_category.children)[3].strip()),
                tuple(bin_category.children)[1].text.strip(),
                icon=ICON_MAP.get(tuple(bin_category.children)[1].text.strip()),
            )
            for bin_category in bin_categories
        ]
