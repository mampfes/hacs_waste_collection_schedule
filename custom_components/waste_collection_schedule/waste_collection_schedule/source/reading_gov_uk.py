from datetime import date, datetime
from typing import List

import requests
from waste_collection_schedule import Collection

TITLE = "Reading Council"
DESCRIPTION = "Source for reading.gov.uk services for Reading Council"
URL = "https://reading.gov.uk"
TEST_CASES = {
    "known_uprn": {"uprn": "310027679"},
    "known_uprn as number": {"uprn": 310027679},
    "unknown_uprn_by_number": {"postcode": "RG31 5PN", "housenameornumber": "65"},
    "unknown_uprn_by_number as number": {"postcode": "RG31 5PN", "housenameornumber": 65}
}

ICONS = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food Waste": "mdi:food",
    "Garden Waste": "mdi:tree"
}

COLLECTIONS = {
    "Domestic Waste Collection Service": "Rubbish",
    "Recycling Collection Service": "Recycling",
    "Food Waste Collection Service": "Food Waste",
    "Garden Waste Collection Service": "Garden Waste"
}

SEARCH_URLS = {
    "UPRN": "https://api.reading.gov.uk/rbc/getaddresses",
    "COLLECTION": "https://api.reading.gov.uk/api/collections"
}


class Source:
    def __init__(
        self, uprn=None, postcode=None, housenameornumber=None
    ):
        self._postcode = postcode
        self._housenameornumber = str(housenameornumber)
        self._uprn = uprn

    def fetch(self) -> List[Collection]:
        if self._uprn is None:
            self._uprn = self.get_uprn()
        resp = requests.get(f"{SEARCH_URLS['COLLECTION']}/{self._uprn}")
        return [self.parse_collection(col) for col in resp.json()["collections"]]

    def get_uprn(self) -> str:
        resp = requests.get(f"{SEARCH_URLS['UPRN']}/{self._postcode}")
        addresses = resp.json()["Addresses"]
        address = next(filter(self.filter_addresses, addresses), None)
        if address is None:
            raise Exception(f"House {self._housenameornumber} not found for postcode {self._postcode}")
        return address["AccountSiteUprn"]

    def filter_addresses(self, address) -> bool:
        nameornum, _ = address["SiteShortAddress"].split(f", {address['SiteAddress2']}, ")
        return self._housenameornumber == nameornum

    def parse_collection(self, col) -> Collection:
        dt = datetime.strptime(col["date"], "%d/%m/%Y %H:%M:%S").date()
        waste_type = COLLECTIONS[col["service"]]
        icon = ICONS[waste_type]

        return Collection(date=dt, t=waste_type, icon=icon)
