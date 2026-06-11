from datetime import datetime
from typing import Any, List, Mapping, Optional

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
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

API_BASE_URL = "https://api.bathnes.gov.uk/webapi/api/{}"
API_COLLECTION_SUMMARY_URL = API_BASE_URL.format(
    "BinsAPI/v2/BartecFeaturesandSchedules/CollectionSummary/{uprn}"
)
API_ADDRESSES_SEARCH_URL = API_BASE_URL.format(
    "AddressesAPI/v2/search/{postcode}/150/true"
)
REQUEST_TIMEOUT = 10


class Source:
    def __init__(self, uprn=None, postcode=None, housenameornumber=None):
        self._uprn = self._sanitise_uprn_val(uprn)
        self._postcode = self._sanitise_search_val(postcode)
        self._housenameornumber = self._sanitise_search_val(housenameornumber)

        if self._uprn is None:
            self._check_required_args(
                "Postcode and house name or number are required if UPRN is not provided",
                ("postcode", self._postcode),
                ("housenameornumber", self._housenameornumber),
            )

    def _sanitise_uprn_val(self, val: Optional[int | str]) -> Optional[int]:
        if val is None:
            return None
        message = "UPRN must be a positive integer if provided"
        try:
            uprn = int(val)
        except (ValueError, TypeError):
            raise SourceArgumentException("uprn", message)
        if uprn <= 0:
            raise SourceArgumentException("uprn", message)
        return uprn

    def _sanitise_search_val(self, val: Optional[str | int]) -> Optional[str]:
        if val is None:
            return None
        stripped = str(val).strip()
        return stripped or None

    def _check_required_args(self, message, *args):
        if missing := [name for name, val in args if not val]:
            raise SourceArgumentExceptionMultiple(missing, message)

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

    def _get_uprn(self) -> int:
        addresses = self._call_api(
            API_ADDRESSES_SEARCH_URL.format(postcode=self._postcode)
        )
        if not addresses:
            raise SourceArgumentNotFound("postcode", self._postcode)

        address = next(filter(self._filter_address, addresses), None)
        if address is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "housenameornumber",
                self._housenameornumber,
                filter(None, [self._address_housenameornumber(a) for a in addresses]),
            )
        return int(address["uprn"])

    def _filter_address(self, address: Mapping[str, Any]) -> bool:
        housenameornumber = self._address_housenameornumber(address)
        return (
            housenameornumber is not None
            and housenameornumber.casefold() == self._housenameornumber.casefold()
        )

    def _address_housenameornumber(self, address: Mapping[str, Any]) -> Optional[str]:
        parts = str(address.get("payment_Address", "")).split("|")
        if len(parts) < 2:
            return None
        return parts[1].strip()

    def _call_api(self, url: str):
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        if r.text.strip() == "":
            raise Exception(f"Empty response from API for url: {url}")
        return r.json()
