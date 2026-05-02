import logging
from datetime import datetime
from typing import Dict

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Dacorum Borough Council"
DESCRIPTION = "Source for Dacorum Borough Council."
URL = "https://www.dacorum.gov.uk/"
TEST_CASES = {
    "Test_001": {"postcode": "HP1 1AB", "uprn": 200004054631},
    "Test_002": {"postcode": "HP4 2EZ", "uprn": "100081111531"},
    "Test_003": {
        "postcode": "HP23 6BE",
        "uprn": "100080716575",
    },
}

ICON_MAP = {
    "grey bin": "mdi:trash-can",
    "grey bin and kerbside caddy": "mdi:trash-can",
    "kerbside caddy": "mdi:food",
    "blue bin": "mdi:recycle",
    "blue bin and kerbside caddy": "mdi:recycle",
    "green bin": "mdi:leaf",
}

API_URL = "https://webapps.dacorum.gov.uk/bincollections/"
FORM_ARG_IDS = [
    "__VIEWSTATE",
    "__EVENTVALIDATION",
    "btnFindAddr",
    "txtBxPCode",
    "lstBxAddrList",
    "MainContent_btnGetSchedules",
]


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode: str = postcode.strip()
        self._uprn: str = str(uprn)

    def _get_form_args(self, soup: BeautifulSoup) -> Dict[str, str]:
        return {
            i.get("name"): i.get("value")
            for i in soup.find_all(["input", "select"])
            if i.get("id") in FORM_ARG_IDS
        }

    def _parse_address_list(self, select_element: Tag) -> Dict[str, str]:
        uprn_addresses = {}
        for row in select_element.children:
            # Ensure child element is a Tag
            if isinstance(row, Tag):
                # Extract uprn from address line
                row_value = row.get("value", "")
                row_parts = row_value.split(";")
                if len(row_parts) == 2:
                    uprn_addresses[row_parts[1]] = row_value

        return uprn_addresses

    def _parse_collection_entry(self, div: Tag) -> Collection | None:
        # bin types are in strong tags
        for strong in div.find_all("strong"):
            bin_type = strong.get_text(strip=True)
            # skip any non-bin finds
            if "bin" not in bin_type.lower():
                continue
            # Find the nearest following cell containing a date
            date_cell = strong.find_parent("div").find_next(
                "div", string=lambda s: s and "Next collection on" in s
            )
            if date_cell:
                collection_date = date_cell.find_next("div").get_text(strip=True)
            # set bin icon
            bin_type_icon = ICON_MAP.get(bin_type.lower())
            # try and add the collection details
            try:
                dt = datetime.strptime(collection_date, "%a, %d %b %Y").date()
                return Collection(date=dt, t=bin_type, icon=bin_type_icon)
            except ValueError:
                return None
        return None

    def fetch(self) -> list[Collection]:
        # Start a session and fetch state args
        session = requests.Session()
        r = session.get(API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        postcode_input = soup.find(id="txtBxPCode")
        if postcode_input is None:
            raise Exception("Postcode input tag not found")

        # Fetch addresses for postcode
        postcode_input["value"] = self._postcode
        r = session.post(API_URL, data=self._get_form_args(soup))
        soup = BeautifulSoup(r.text, features="html.parser")
        address_input = soup.find(id="lstBxAddrList")
        if address_input is None:
            raise Exception("Address input tag not found")

        # Find address value for uprn
        addresses = self._parse_address_list(address_input)
        if self._uprn not in addresses:
            raise Exception(
                f"uprn '{self._uprn}' not found for postcode '{self._postcode}'"
            )
        address_input["value"] = addresses[self._uprn]

        # Find collections for address
        r = session.post(API_URL, data=self._get_form_args(soup))
        soup = BeautifulSoup(r.text, features="html.parser")
        collection_content = soup.find("div", id="MainContent_updPnl")
        if collection_content is None:
            raise Exception("MainContent_updPnl tag not found")

        # Parse entries into collections
        collections = []
        entries = collection_content.findChildren("div", recursive=False)
        for e in entries:
            c = self._parse_collection_entry(e)
            if c is not None:
                collections.append(c)

        return collections
