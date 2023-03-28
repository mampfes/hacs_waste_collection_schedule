from datetime import datetime
import requests
import re

from waste_collection_schedule import Collection

TITLE = "Fenland District Council"
DESCRIPTION = "Source script for fenland.gov.uk services for Fenland"
URL = "https://www.fenland.gov.uk/"
TEST_CASES = {
    "Address1": {"post_code": "PE13 1JR", "house_number": "Flat 1"},
    "Address2": {"post_code": "PE15 0SD", "house_number": 1}
}

API_URLS = {
    "address_search": "https://www.fenland.gov.uk/find?type=postcodesearch&postcode={}",
    "collection": "https://www.fenland.gov.uk/find?type=loadlayer&layerId=2&uprn={uprn}&lat={lat}&lng={lng}",
}

ICON_MAP = {
    "Empty Bin GREEN 240": "mdi:trash-can",
    "Empty Bin REFUSE SACK": "mdi:trash-can",
    "Empty Bin BLUE 240": "mdi:recycle",
    "Empty Bin RECYCLING SACK": "mdi:recycle",
    "Empty Bin BROWN 240": "mdi:leaf",
}


class Source:
    def __init__(self, post_code: str, house_number: str):
        self._post_code = post_code
        self._house_number = house_number

    def fetch(self):

        r = requests.get(
            API_URLS["address_search"].format(self._post_code), headers={"Accept":"application/json"}
        )
        r.raise_for_status()
        addresses = r.json()

        address_ids = [
            address for address in addresses if re.search(f"^{self._house_number} ", address["line1"]) # House numbers are not separated from address line
        ]

        if len(address_ids) == 0:
            print(addresses)
            raise Exception(f"Could not find address :: Post Code: {self._post_code} House Number: {self._house_number}")

        r = requests.get(
            API_URLS["collection"].format(uprn = address_ids[0]["udprn"], lat = address_ids[0]["latitude"], lng = address_ids[0]["longitude"]), headers={"Accept":"application/json"}
        )
        r.raise_for_status()
        collections = r.json()["features"][0]["properties"]["upcoming"]

        entries = []

        for collectionDate in collections:
            for collection in collectionDate["collections"]:
                entries.append(
                    Collection(
                        date = datetime.strptime(
                                collectionDate["date"], "%Y-%m-%dT%H:%M:%SZ"
                            ).date(),
                        t = collection["desc"],
                        icon = ICON_MAP.get(collection["name"]),
                    )
                )

        return entries