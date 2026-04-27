from datetime import datetime
from typing import List

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Reading Council"
DESCRIPTION = "Source for reading.gov.uk services for Reading Council"
URL = "https://reading.gov.uk"
TEST_CASES = {
    "known_uprn": {"uprn": "310027679"},
    "known_uprn as number": {"uprn": 310027679},
    "unknown_uprn_by_number": {"postcode": "RG31 5PN", "house_number_or_name": "65"},
    "unknown_uprn_by_number as number": {
        "postcode": "RG31 5PN",
        "house_number_or_name": 65,
    },
}

ICONS = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food Waste": "mdi:food",
    "Garden Waste": "mdi:tree",
}

COLLECTIONS = {
    "Domestic Waste Collection Service": "Rubbish",
    "Recycling Collection Service": "Recycling",
    "Food Waste Collection Service": "Food Waste",
    "Garden Waste Collection Service": "Garden Waste",
}

SEARCH_URLS = {
    "UPRN": "https://api.reading.gov.uk/rbc/getaddresses",
    "COLLECTION": "https://api.reading.gov.uk/api/collections",
}


class Source:
    def __init__(self, uprn=None, postcode=None, house_number_or_name=None):
        self._postcode = postcode
        self._housenameornumber = str(house_number_or_name)
        self._uprn = uprn
        if not any((uprn, postcode and house_number_or_name)):
            errors = []
            if postcode:
                errors.append("house_number_or_name")
            elif house_number_or_name:
                errors.append("postcode")
            else:
                errors = ["uprn", "postcode", "house_number_or_name"]
            raise SourceArgumentExceptionMultiple(
                errors,
                "Must provide either a UPRN or both the Postcode and House Name or Number",
            )

    def fetch(self) -> List[Collection]:
        if self._uprn is None:
            self._uprn = self.get_uprn()
        resp = requests.get(f"{SEARCH_URLS['COLLECTION']}/{self._uprn}")
        return [self.parse_collection(col) for col in resp.json()["collections"]]

    def get_uprn(self) -> str:
        resp = requests.get(f"{SEARCH_URLS['UPRN']}/{self._postcode}")
        addresses = resp.json()["Addresses"]
        if addresses is None:
            raise SourceArgumentNotFound("postcode", self._postcode)
        address = next(filter(self.filter_addresses, addresses), None)
        if address is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number_or_name",
                self._housenameornumber,
                {self.extract_nameornum(a) for a in addresses},
            )
        return address["AccountSiteUprn"]

    def extract_nameornum(self, address) -> str:
        nameornum, _ = address["SiteShortAddress"].split(
            f", {address['SiteAddress2']}, "
        )
        return nameornum

    def filter_addresses(self, address) -> bool:
        nameornum = self.extract_nameornum(address)
        return self._housenameornumber == nameornum

    def parse_collection(self, col) -> Collection:
        dt = datetime.strptime(col["date"], "%d/%m/%Y %H:%M:%S").date()
        waste_type = COLLECTIONS[col["service"]]
        icon = ICONS[waste_type]

        return Collection(date=dt, t=waste_type, icon=icon)
