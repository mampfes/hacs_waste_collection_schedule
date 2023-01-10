import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Ashfield District Council"
DESCRIPTION = "Source for ashfield.gov.uk, Ashfield District Council, UK"
URL = "https://www.ashfield.gov.uk"
TEST_CASES = {
    "11 Maun View Gardens, Sutton-in-Ashfield": {"uprn": 10001336299},
    "4A Station Street, Kirkby-in-Ashfield": {"post_code": "NG177AR", "number": "4A"},
    "Ashfield District Council": {
        "post_code": "NG17 8DA",
        "name": "Ashfield District Council",
    },
}

API_URLS = {
    "address_search": "https://www.ashfield.gov.uk/api/powersuite/getaddresses/{postcode}",
    "collection": "https://www.ashfield.gov.uk/api/powersuite/GetCollectionByUprnAndDate/{uprn}",
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
            # look up the UPRN for the address
            q = str(API_URLS["address_search"]).format(postcode=self._post_code)
            r = requests.get(q)
            r.raise_for_status()
            addresses = r.json()["data"]

            if self._name:
                self._uprn = [
                    int(x["AccountSiteUprn"])
                    for x in addresses
                    if x["SiteAddressName"].capitalize() == self._name.capitalize()
                ][0]
            elif self._number:
                self._uprn = [
                    int(x["AccountSiteUprn"])
                    for x in addresses
                    if x["SiteAddressNumber"] == self._number
                ][0]

            if not self._uprn:
                raise Exception(
                    f"Could not find address {self._post_code} {self._number}{self._name}"
                )

        q = str(API_URLS["collection"]).format(uprn=self._uprn)

        r = requests.get(q)
        r.raise_for_status()

        collections = r.json()["data"]
        entries = []

        if collections:
            for collection in collections:
                entries.append(
                    Collection(
                        date=datetime.datetime.strptime(
                            collection["Date"], "%d/%m/%Y %H:%M:%S"
                        ).date(),
                        t=NAMES.get(collection["Service"]),
                        icon=ICON_MAP.get(collection["Service"]),
                    )
                )

        return entries
