from datetime import datetime
from typing import List

import requests

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Bath & North East Somerset Council"
DESCRIPTION = (
    "Source for bathnes.gov.uk services for Bath & North East Somerset Council"
)
URL = "https://bathnes.gov.uk"
TEST_CASES = {
    "uprn": {"uprn": "10001138699"},
    "houseNumber": {"postcode": "BA1 2LR", "housenameornumber": 1},
    "houseName": {"postcode": "BA1 5SX", "housenameornumber": "St Stephen's Church"},
}

TYPES = {
    "Residual": {"icon": "mdi:trash-can", "alias": "Rubbish"},
    "Recycling": {"icon": "mdi:recycle", "alias": "Recycling"},
    "Garden": {"icon": "mdi:leaf", "alias": "Garden Waste"},
}

API_COLLECTION_SUMMARY_URL = "https://api.bathnes.gov.uk/webapi/api/BinsAPI/v2/BartecFeaturesandSchedules/CollectionSummary/{uprn}"
API_ADDRESSES_SEARCH_URL = "https://api.bathnes.gov.uk/webapi/api/AddressesAPI/v2/search/{postcode}/150/true"

class Source:
    def __init__(self, uprn=None, postcode=None, housenameornumber=None):
        self._postcode = postcode
        self._housenameornumber = str(housenameornumber)
        self._uprn = uprn

    def fetch(self) -> List[Collection]:
        if self._uprn is None:  
            self._uprn = self._get_uprn()

        entries = self._call_api(API_COLLECTION_SUMMARY_URL.format(uprn=self._uprn))
        return [
            Collection(
                date=datetime.fromisoformat(isodate).date(),
                t=props["alias"],
                icon=props["icon"],
            )
            for entry in entries
            if (props := TYPES.get(entry.get("featureType")))
            for date_type in ["previous", "next"]
            if (isodate := entry.get(f"{date_type}CollectionDate"))
        ]

    def _get_uprn(self) -> str:
        addresses = self._call_api(API_ADDRESSES_SEARCH_URL.format(postcode=self._postcode))

        address = next(filter(self._filter_addresses, addresses), None)
        if address is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "housenameornumber",
                self._housenameornumber,
                [a["payment_Address"].split("|")[1] for a in addresses],
            )
        return int(address["uprn"])

    def _filter_addresses(self, address) -> bool:
        return f"|{self._housenameornumber.upper()}|" in address["payment_Address"]

    def _call_api(self, url: str):
        r = requests.get(url)
        r.raise_for_status()
        if r.text.strip() == "":
            raise Exception(f"empty response")
        return r.json()
