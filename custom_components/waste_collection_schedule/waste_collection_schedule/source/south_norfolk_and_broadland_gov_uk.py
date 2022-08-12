import json
import re
from datetime import date
from time import strptime
from typing import List
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup as soup
from waste_collection_schedule import Collection

TITLE = "South Norfolk and Broadland Council UK"
DESCRIPTION = "Source for southnorfolkandbroadland.gov.uk services for South Norfolk and Broadland, UK"

URL = "https://area.southnorfolkandbroadland.gov.uk/"
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
            "Authority": "2610"
        }
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
            "Authority": "2610"
        }
    }
}

ICONS = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden (if applicable)": "mdi:leaf"
}

matcher = re.compile(r"^([A-Z][a-z]+) (\d{1,2}) ([A-Z][a-z]+) (\d{4})$")
def parse_date(date_str: str) -> date:
    match = matcher.match(date_str)
    return date(
        int(match.group(4)),
        strptime(match.group(3)[:3], "%b").tm_mon,
        int(match.group(2))
    )


class Source:
    _address_payload: dict

    def __init__(self, address_payload: dict):
        self._address_payload = address_payload

    def fetch(self) -> List[Collection]:
        r = requests.get(URL, headers={"Cookie": f"MyArea.Data={quote(json.dumps(self._address_payload))}"})
        r.raise_for_status()

        page = soup(r.text, "html.parser")
        bins_card = page.find("h3", text="Bins").parent
        bin_categories = bins_card.find_all("div", {"class": "card-text"})
        return [
            Collection(
                parse_date(tuple(bin_category.children)[3].strip()),
                tuple(bin_category.children)[1].text.strip(),
                icon=ICONS.get(tuple(bin_category.children)[1].text.strip())
            )
            for bin_category
            in bin_categories
        ]
