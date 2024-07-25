import re
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)

TITLE = "Fenland District Council"
DESCRIPTION = "Source script for fenland.gov.uk services for Fenland"
URL = "https://www.fenland.gov.uk/"
TEST_CASES = {
    "Address1": {"post_code": "PE13 1JR", "house_number": "Flat 1"},
    "Address2": {"post_code": "PE15 0SD", "house_number": 1},
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
        params = {"type": "postcodesearch", "postcode": self._post_code}
        r = requests.get(
            "https://www.fenland.gov.uk/find",
            params=params,
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()

        addresses = r.json()
        if len(addresses) == 0:
            raise SourceArgumentNotFound("post_code", self._post_code)

        address_ids = [
            address
            for address in addresses
            if re.search(
                f"^{self._house_number} ", address["line1"]
            )  # House numbers are not separated from address line
        ]

        if len(address_ids) == 0:
            raise SourceArgAmbiguousWithSuggestions(
                "house_number",
                self._house_number,
                [(address["line1"].split(" ")[0]) for address in addresses],
            )

        params = {
            "type": "loadlayer",
            "layerId": 2,
            "uprn": address_ids[0]["udprn"],
            "lat": address_ids[0]["latitude"],
            "lng": address_ids[0]["longitude"],
        }
        r = requests.get(
            "https://www.fenland.gov.uk/find",
            params=params,
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()

        entries = []

        collections = r.json()["features"][0]["properties"]["upcoming"]
        for collection_date_dict in collections:
            collection_date = datetime.strptime(
                collection_date_dict["date"], "%Y-%m-%dT%H:%M:%SZ"
            )
            if collection_date.hour == 23:
                collection_date = (timedelta(days=1) + collection_date).date()
            else:
                collection_date = collection_date.date()
            for collection in collection_date_dict["collections"]:
                entries.append(
                    Collection(
                        date=collection_date,
                        t=collection["desc"],
                        icon=ICON_MAP.get(collection["name"]),
                    )
                )

        return entries
