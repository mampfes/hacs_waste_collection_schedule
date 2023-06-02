from datetime import date, datetime
from typing import List

import requests
from waste_collection_schedule import Collection

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
    "houseName": {"postcode": "BA2 9AZ", "housenameornumber": "All Saints Church"},
}

TYPES = {
    "residual": {"icon": "mdi:trash-can", "alias": "Rubbish"},
    "recycling": {"icon": "mdi:recycle", "alias": "Recycling"},
    "organic": {"icon": "mdi:leaf", "alias": "Garden Waste"},
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

        info = session.get(
            f"https://www.bathnes.gov.uk/webapi/api/BinsAPI/v2/getbartecroute/{self._uprn}/true"
        ).json()

        entries = []
        for type, props in TYPES.items():
            for dateType in ["Previous", "Next"]:
                if info.get(f"{type}Route", "NS") == "NS":
                    continue

                entries.append(
                    Collection(
                        date=datetime.fromisoformat(
                            info[f"{type}{dateType}Date"]
                        ).date(),
                        t=props["alias"],
                        icon=props["icon"],
                    )
                )

        return entries

    def get_uprn(self, session) -> str:
        addresses = session.get(
            f"https://www.bathnes.gov.uk/webapi/api/AddressesAPI/v2/search/{self._postcode}/150/true"
        ).json()
        address = next(filter(self.filter_addresses, addresses), None)
        if address is None:
            raise Exception(
                f"House {self._housenameornumber} not found for postcode {self._postcode}"
            )
        return address["uprn"]

    def filter_addresses(self, address) -> bool:
        return f"|{self._housenameornumber.upper()}|" in address["payment_Address"]
