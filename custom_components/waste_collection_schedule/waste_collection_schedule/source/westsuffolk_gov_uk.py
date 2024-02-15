import re

import requests
from bs4 import BeautifulSoup, Tag
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "West Suffolk Council"
DESCRIPTION = "Source for West Suffolk Council."
URL = "https://westsuffolk.gov.uk/"
TEST_CASES = {
    "Flat, The Flying Shuttle, Three Counties Way, Withersfield, CB9 7FB": {
        "uprn": 10090739388
    },
    "Haere Mai, The Street, Troston, IP31 1EW": {"uprn": "100091387226"},
}


ICON_MAP = {
    "Black bin": "mdi:trash-can",
    "Brown bin": "mdi:leaf",
    "Blue bin": "mdi:recycle",
}


API_URL = "https://maps.westsuffolk.gov.uk/MyWestSuffolk.aspx"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        session = requests.session()
        args = {"UniqueId": self._uprn, "action": "SetAddress"}

        # get json file
        r = session.get(API_URL, params=args)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        collections_div = soup.find(
            "", text=re.compile(r"Your next bin collection days", re.IGNORECASE)
        ).find_next_sibling("div", class_="atPanelData")

        bin_type = None
        entries = []

        for collection in collections_div.contents:
            if isinstance(collection, Tag):
                if collection.name == "strong":
                    bin_type = " ".join(
                        a.strip()
                        for a in collection.text.strip().strip(":").split("\n")
                    )
                continue

            collection = collection.strip()
            date_str = collection.strip()
            # date: Saturday 30th December
            coll_date = parser.parse(date_str).date()
            entries.append(
                Collection(date=coll_date, t=bin_type, icon=ICON_MAP.get(bin_type))
            )
        return entries
