import datetime

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Ashfield District Council"
DESCRIPTION = "Source for ashfield.gov.uk, Ashfield District Council, UK"
URL = "https://www.ashfield.gov.uk"
TEST_CASES = {
    "11 Maun View Gardens, Sutton-in-Ashfield": {"uprn": 10001336299},
    "101 Main Street, Huthwaite": {"post_code": "NG17 2LQ", "uprn": "100031253415"},
    "1 Acacia Avenue, Kirkby-in-Ashfield": {"post_code": "NG17 9BH", "number": "1"},
    "Council Offices, Kirkby-in-Ashfield": {
        "post_code": "NG178ZA",
        "name": "COUNCIL OFFICES",
    },
}

API_URLS = {
    "address_search": "https://www.ashfield.gov.uk/api/address/search/{postcode}",
    "collection": "https://www.ashfield.gov.uk/api/address/collections/{uprn}",
}

ICON_MAP = {
    "Residual Waste Collection Service": "mdi:trash-can",
    "Domestic Recycling Collection Service": "mdi:recycle",
    "Domestic Glass Collection Service": "mdi:glass-fragile",
    "Garden Waste Collection Service": "mdi:leaf",
}

NAMES = {
    "Residual Waste Collection Service": "Red (rubbish)",
    "Domestic Recycling Collection Service": "Green (recycling)",
    "Domestic Glass Collection Service": "Blue (glass)",
    "Garden Waste Collection Service": "Brown (garden)",
}


class Source:
    def __init__(self, post_code=None, number=None, name=None, uprn=None):
        self._post_code = post_code
        self._number = number
        self._name = name
        self._uprn = uprn

    def fetch(self):
        if not self._uprn:
            if not self._post_code:
                raise ValueError("post_code is required when uprn is not provided")
            if not (self._name or self._number):
                raise ValueError(
                    "Either name or number must be provided when uprn is not provided"
                )
            # look up the UPRN for the address
            q = str(API_URLS["address_search"]).format(postcode=self._post_code)
            r = requests.get(q, timeout=30)
            r.raise_for_status()
            addresses = r.json()["results"]

            if not addresses:
                raise SourceArgumentNotFound("post_code", self._post_code)

            matching = []
            if self._name:
                name_cf = self._name.casefold()
                for x in addresses:
                    dpa = x.get("DPA") or {}
                    building_name = dpa.get("BUILDING_NAME")
                    if building_name and building_name.casefold() == name_cf:
                        matching.append(x)
            elif self._number:
                for x in addresses:
                    dpa = x.get("DPA") or {}
                    if dpa.get("BUILDING_NUMBER") == self._number:
                        matching.append(x)

            if matching:
                first_dpa = matching[0].get("DPA") or {}
                uprn_value = first_dpa.get("UPRN")
                if uprn_value:
                    self._uprn = int(uprn_value)

            if not self._uprn:
                raise SourceArgumentNotFoundWithSuggestions(
                    argument=(
                        "name"
                        if self._name
                        else "number" if self._number else "post_code"
                    ),
                    value=self._name or self._number or self._post_code,
                    suggestions=[
                        f"{(x.get('DPA') or {}).get('BUILDING_NUMBER', '')} {(x.get('DPA') or {}).get('BUILDING_NAME', '')}".strip()
                        for x in addresses
                    ],
                )
        else:
            # Ensure UPRN is an integer
            self._uprn = int(self._uprn)

        q = str(API_URLS["collection"]).format(uprn=self._uprn)

        r = requests.get(q, timeout=30)
        r.raise_for_status()

        collections = r.json()["collections"]
        entries = []

        if collections:
            for collection in collections:
                entries.append(
                    Collection(
                        date=datetime.datetime.strptime(
                            collection["date"], "%d/%m/%Y %H:%M:%S"
                        ).date(),
                        t=NAMES.get(collection["service"], collection["service"]),
                        icon=ICON_MAP.get(collection["service"]),
                    )
                )

        return entries
