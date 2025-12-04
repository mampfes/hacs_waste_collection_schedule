import requests
from bs4 import BeautifulSoup, Tag
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North East Lincolnshire Council"
DESCRIPTION = "Source for North East Lincolnshire Council."
URL = "https://www.nelincs.gov.uk/"
TEST_CASES = {"11042949": {"uprn": 11042949}, "11043243": {"uprn": "11043243"}}


HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": """Fill in your address details at [North East Lincolnshire Council's Find My Address](https://www.nelincs.gov.uk/find-my-address/), the Unique Property Reference Number (UPRN) will be shown in the URL field when you see your collection schedule. (e.g. `https://www.nelincs.gov.uk/?s=DN40+1JU&uprn=11043243` where `11043243` is the UPRN).

Another easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
"""
}


ICON_MAP = {
    "household waste": "mdi:trash-can",
    "garden": "mdi:leaf",
    "paper": "mdi:package-variant",
    "cans, plastic & glass": "mdi:recycle",
}


API_URL = "https://www.nelincs.gov.uk/refuse-collection-schedule/"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self) -> list[Collection]:
        args = {"uprn": self._uprn}

        r = requests.get(API_URL, params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        heading_i = soup.select_one("i.fa-trash")
        if not heading_i:
            raise ValueError("No collection data found for the provided UPRN.")
        collection_div = heading_i.find_parent("div")
        if not isinstance(collection_div, Tag):
            raise ValueError("No collection data found for the provided UPRN.")

        entries = []
        for heading, col_list in zip(
            collection_div.select("div.h4"), collection_div.select("ul")
        ):
            bin_type = heading.text.strip()
            icon = ICON_MAP.get(bin_type.casefold())  # Collection icon
            for li in col_list.select("li"):
                date_str = li.text.strip()
                date_ = parser.parse(date_str, dayfirst=True).date()
                entries.append(Collection(date=date_, t=bin_type, icon=icon))

        return entries
