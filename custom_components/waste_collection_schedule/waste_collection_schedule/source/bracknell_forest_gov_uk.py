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
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
    "Food": "mdi:food-apple",
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
        self.house_number = house_number

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
            if address["Description"].startswith(f"{self.house_number} ")
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
        for waste_type in ICON_MAP.keys():
            try:
                entries.append(
                    Collection(
                        date=parser.parse(
                            next(
                                collection
                                for collection in collections
                                if collection["round"] == waste_type
                            )["firstDate"]["date"]
                        ).date(),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )
            except (StopIteration, TypeError):
                pass

        return entries
