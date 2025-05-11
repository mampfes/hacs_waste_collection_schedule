import json

import requests
from dateutil import parser
from waste_collection_schedule import Collection

TITLE = "Bracknell Forest Council"
DESCRIPTION = "Bracknell Forest Council, UK - Waste Collection"
URL = "https://selfservice.mybfc.bracknell-forest.gov.uk"
TEST_CASES = {
    "44 Kennel Lane": {"house_number": "44", "post_code": "RG42 2HB"},
    "28 Kennel Lane": {"house_number": "28", "post_code": "RG42 2HB"},
    "32 Ashbourne": {"house_number": "32", "post_code": "RG12 8SG"},
    "1 Acacia Avenue": {"house_number": "1", "post_code": "GU47 0RU"},
    "Myrtle, 39 New Wokingham Road": {
        "house_number": "Myrtle",
        "post_code": "RG45 6JG",
    },
}

ICON_MAP = {
    "general waste": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "garden": "mdi:leaf",
    "food": "mdi:food-apple",
}


class Source:
    def __init__(self, post_code: str, house_number: str):
        self.params = {
            "webpage_subpage_id": "PAG0000570FEFFB1",
            "webpage_token": "390170046582b0e3d7ca68ef1d6b4829ccff0b1ae9c531047219c6f9b5295738",
            "widget_action": "handle_event",
        }
        self.headers = {
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        }
        self.data = {
            "action_cell_id": "PCL0003988FEFFB1",
            "action_page_id": "PAG0000570FEFFB1",
        }
        self.url = f"{URL}/w/webpage/waste-collection-days"
        self.post_code = post_code
        self.house_number = str(house_number)

        if self.house_number.isnumeric():
            self.house_number = f"{self.house_number} "

    def fetch(self):
        address_lookup = requests.post(
            self.url,
            params=self.params,
            headers=self.headers,
            data={
                "code_action": "find_addresses",
                "code_params": json.dumps({"search": self.post_code}),
            }
            | self.data,
        )
        address_lookup.raise_for_status()
        addresses = address_lookup.json()["response"]["addresses"]["items"]
        id = next(
            address
            for address in addresses
            if address["Description"].upper().startswith(self.house_number.upper())
        )["Id"]

        collection_lookup = requests.post(
            self.url,
            params=self.params,
            headers=self.headers,
            data={
                "code_action": "find_rounds",
                "code_params": json.dumps({"addressId": id}),
            }
            | self.data,
        )
        collection_lookup.raise_for_status()
        collections = collection_lookup.json()["response"]["collections"]
        entries = []
        for collection_entry in collections:
            try:
                coll_day = parser.parse(collection_entry["firstDate"]["date"]).date()
            except KeyError:
                continue
            entries.append(
                Collection(
                    date=coll_day,
                    t=collection_entry["round"],
                    icon=ICON_MAP.get(collection_entry["round"].lower()),
                )
            )

        return entries
