from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# mostly copied from braintree_gov_uk

TITLE = "Tonbridge and Malling Borough Council"
DESCRIPTION = "Tonbridge and Malling Borough Council, UK - Waste Collection"
URL = "https://www.tmbc.gov.uk"
TEST_CASES = {
    "High Street, West Malling": {
        "address": "138 High Street",
        "post_code": "ME19 6NE",
    },
    "Nutfields, Ightham, Sevenoaks": {
        "address": "5 Nutfields, Ightham, Sevenoaks",
        "post_code": "TN15 9EA",
    },
}

ICON_MAP = {
    "Black domestic waste": "mdi:trash-can",
    "Green recycling": "mdi:recycle",
    "Brown garden waste": "mdi:leaf",
    "Food waste": "mdi:food-apple",
}


class Source:
    def __init__(self, post_code: str, address: str):
        self.post_code = post_code
        self.address = address
        self.url = f"{URL}/xfp/form/167"
        self.form_data = {
            "q752eec300b2ffef2757e4536b77b07061842041a_0_0": (None, post_code),
            "page": (None, 128),
        }

    def fetch(self):
        address_lookup = requests.post(
            "https://www.tmbc.gov.uk/xfp/form/167", files=self.form_data
        )
        address_lookup.raise_for_status()
        addresses = {}
        for address in BeautifulSoup(address_lookup.text, "html.parser").find_all(
            "option"
        ):
            if "..." not in address["value"]:
                addresses[address["value"]] = address.text.strip()
        id = [
            address
            for address in addresses
            if addresses[address].startswith(self.address)
        ]
        if len(id) == 0:
            raise Exception("Address not found")
        if len(id) > 1:
            raise Exception("Address is not unique")
        id = id[0]

        self.form_data["q752eec300b2ffef2757e4536b77b07061842041a_1_0"] = (None, id)
        self.form_data["next"] = (None, "Next")
        collection_lookup = requests.post(
            "https://www.tmbc.gov.uk/xfp/form/167", files=self.form_data
        )
        collection_lookup.raise_for_status()
        entries = []
        for rows in (
            BeautifulSoup(collection_lookup.text, "html.parser")
            .find("table", class_="waste-collections-table")
            .find("tbody")
            .find_all("tr")
        ):
            date_td = rows.find_all("td")[0]
            bins_td = rows.find_all("td")[1]

            date = parser.parse(date_td.text.strip(), dayfirst=True).date()
            if datetime.now().month == 12 and date.month in (1, 2):
                date = date.replace(year=date.year + 1)
            for bin in bins_td.find("div", class_="collections").findAll("p"):
                bin = bin.text.strip()
                entries.append(
                    Collection(
                        date=date,
                        t=bin,
                        icon=ICON_MAP.get(bin),
                    )
                )

        return entries
