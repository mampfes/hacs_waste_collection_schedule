import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Cambridge City Council"
DESCRIPTION = (
    "Source for cambridge.gov.uk services for Cambridge and part of Cambridgeshire"
)
URL = "https://cambridge.gov.uk"
TEST_CASES = {
    "houseNumber": {"post_code": "CB13JD", "number": 37},
    "houseName": {"post_code": "cb215hd", "number": "ROSEMARY HOUSE"},
}

API_URLS = {
    "address_search": "https://servicelayer3c.azure-api.net/wastecalendar/address/search/",
    "collection": "https://servicelayer3c.azure-api.net/wastecalendar/collection/search/{}/",
}

ICON_MAP = {
    "DOMESTIC": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "ORGANIC": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, post_code: str, number: str):
        self._post_code = post_code
        self._number = str(number).capitalize()

    def fetch(self):
        # fetch location id
        r = requests.get(
            API_URLS["address_search"], params={"postCode": self._post_code}
        )
        r.raise_for_status()
        addresses = r.json()

        address_ids = [
            x["id"] for x in addresses if x["houseNumber"].capitalize() == self._number
        ]

        if len(address_ids) == 0:
            raise Exception(f"Could not find address {self._post_code} {self._number}")

        q = str(API_URLS["collection"]).format(address_ids[0])
        r = requests.get(q)
        r.raise_for_status()

        collections = r.json()["collections"]
        entries = []

        for collection in collections:
            for round_type in collection["roundTypes"]:
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            collection["date"], "%Y-%m-%dT%H:%M:%SZ"
                        ).date(),
                        t=round_type.title(),
                        icon=ICON_MAP.get(round_type),
                    )
                )

        return entries
