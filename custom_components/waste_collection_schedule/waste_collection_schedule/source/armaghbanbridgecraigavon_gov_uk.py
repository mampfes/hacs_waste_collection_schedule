from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection

TITLE = "Armagh City Banbridge & Craigavon"
DESCRIPTION = "Source for Armagh City Banbridge & Craigavon."
URL = "https://www.armaghbanbridgecraigavon.gov.uk"
TEST_CASES = {
    "BT667ES": {"address_id": 185622007},
    "BT63 5GY": {"address_id": "187318004"},
}


ICON_MAP = {
    "Domestic": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden & Food": "mdi:leaf",
}


API_URL = "https://www.armaghbanbridgecraigavon.gov.uk/resident/binday-result/"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find the parameter of your address using https://www.armaghbanbridgecraigavon.gov.uk/resident/when-is-my-bin-day/, after selecting your address. The address ID is the number at the end of the URL after `address=`.",
}


class Source:
    def __init__(self, address_id: int):
        self._address_id: int = address_id

    def fetch(self) -> list[Collection]:
        args = {"address": self._address_id}

        r = requests.get(API_URL, params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        headings = soup.select("div.heading > h2 > i.fa")
        if not headings:
            raise Exception("No headings found while parsing the response HTML.")

        entries = []

        for heading in headings:
            heading_tag = heading.parent
            if not isinstance(heading_tag, Tag):
                raise Exception("Heading is not a valid HTML tag.")

            bin_type = heading_tag.text.replace("Collections", "").strip()
            icon = ICON_MAP.get(bin_type)  # Collection icon
            heading_col = heading_tag.find_parent("div", class_="col-sm-12")
            if not heading_col:
                raise Exception("No parent column found for the bin type.")

            collection_col = heading_col.find_next_sibling()
            if not isinstance(collection_col, Tag):
                raise Exception(
                    "Could not find collection dates while parsing the response HTML."
                )
            for h4 in collection_col.select("h4"):
                date_str = h4.text.strip()
                date = datetime.strptime(date_str, "%d/%m/%Y").date()

                entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
