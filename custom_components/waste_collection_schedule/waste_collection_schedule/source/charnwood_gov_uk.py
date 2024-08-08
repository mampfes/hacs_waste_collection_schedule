from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Charnwood"
DESCRIPTION = "Source for Charnwood."
URL = "https://www.charnwood.gov.uk/"
TEST_CASES = {
    "111, Main Street, Swithland": {"address": "111, Main Street, Swithland"},
    "2, The Banks, Sileby": {"address": "2 The Banks, Sileby"},
}


ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Garden Waste": "mdi:leaf",
    "Recycling": "mdi:recycle",
}


API_URL = "https://my.charnwood.gov.uk/my-property-finder"
SEARCH_URL = "https://my.charnwood.gov.uk/data/ac/addresses.json"


class Source:
    def __init__(self, address: str):
        self._address_search: str = address
        self._address_compare: str = address.lower().replace(" ", "").replace(",", "")
        self._address_id = None

    def _match_address(self, address: str) -> bool:
        return (
            address.lower().replace(" ", "").replace(",", "") == self._address_compare
        )

    @staticmethod
    def _parse_date(date_str: str) -> date:
        if date_str.lower() == "today":
            return date.today()

        if date_str.lower() == "tomorrow":
            return date.today() + timedelta(days=1)

        return parse(date_str).date()

    def _get_address_id(self):
        params = {
            "term": self._address_search,
        }
        r = requests.get(SEARCH_URL, params=params)
        r.raise_for_status()
        data = r.json()
        if not data:
            raise ValueError(
                "No address found for search term: " + self._address_search
            )

        for address in data:
            if self._match_address(address["label"]):
                self._address_id = address["value"]
                return

        raise ValueError(
            "Address not found, use one of the following: "
            + ", ".join([address["label"] for address in data])
        )

    def fetch(self) -> list[Collection]:
        fresh_id = False
        if not self._address_id:
            self._get_address_id()
            fresh_id = True

        try:
            return self._get_collections()
        except Exception:
            if fresh_id:
                raise
            self._get_address_id()
            return self._get_collections()

    def _get_collections(self) -> list[Collection]:
        if not self._address_id:
            raise ValueError("Address not set")

        args = {"address_id": self._address_id}

        # get json file
        r = requests.get(API_URL, params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        collection_panel = soup.find("div", {"class": "refusecollectiondates"})
        if not collection_panel:
            raise ValueError("No collection panel found")
        entries = []

        for li in collection_panel.select("li"):
            date_tag = li.find("strong")
            if not date_tag:
                continue
            date_str = date_tag.text.strip()
            waste_type_tag = date_tag.find_next("a")
            if not waste_type_tag:
                continue
            waste_type = waste_type_tag.text.strip()
            date_ = self._parse_date(date_str)
            entries.append(Collection(date_, waste_type, icon=ICON_MAP.get(waste_type)))

        return entries
