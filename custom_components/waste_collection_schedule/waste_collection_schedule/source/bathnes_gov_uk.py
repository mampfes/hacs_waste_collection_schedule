from datetime import datetime
from typing import List

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
# Include work around for SSL UNSAFE_LEGACY_RENEGOTIATION_DISABLED error
from waste_collection_schedule.service.SSLError import get_legacy_session

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


class Source:
    def __init__(self, uprn=None, postcode=None, housenameornumber=None):
        self._postcode = postcode
        self._housenameornumber = str(housenameornumber)
        self._uprn = uprn

    def fetch(self) -> List[Collection]:
        session = get_legacy_session()

        if self._uprn is None:
            self._uprn = self.get_uprn(session)

        r = session.get(
            f"https://api.bathnes.gov.uk/webapi/api/BinsAPI/v2/BartecFeaturesandSchedules/CollectionSummary/{self._uprn}"
        )
        if r.status_code != 200 or r.text.strip() == "":
            raise Exception(f"could not get collection summary for uprn {self._uprn}")
        entries = r.json()

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

    def get_uprn(self, session) -> str:
        r = session.get(
            f"https://api.bathnes.gov.uk/webapi/api/AddressesAPI/v2/search/{self._postcode}/150/true"
        )
        if r.status_code != 200 or r.text.strip() == "":
            raise Exception(f"could not get addresses for postcode {self._postcode}")
        addresses = r.json()

        address = next(filter(self.filter_addresses, addresses), None)
        if address is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "housenameornumber",
                self._housenameornumber,
                [a["payment_Address"].split("|")[1] for a in addresses],
            )
        return int(address["uprn"])

    def filter_addresses(self, address) -> bool:
        return f"|{self._housenameornumber.upper()}|" in address["payment_Address"]
