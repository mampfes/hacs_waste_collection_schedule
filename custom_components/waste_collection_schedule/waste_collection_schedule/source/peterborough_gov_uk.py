import logging
import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Peterborough City Council"
DESCRIPTION = (
    "Source for peterborough.gov.uk services for Peterborough"
)
URL = "https://peterborough.gov.uk"
TEST_CASES = {
    "houseNumber": {"post_code": "PE57AX", "number": 1},
    "houseName": {"post_code": "PE57AX", "name": "CASTOR HOUSE"},
    "houseUprn": {"uprn": "100090214774"}
}

API_URLS = {
    "address_search": "https://www.peterborough.gov.uk/api/addresses/{postcode}",
    "collection": "https://www.peterborough.gov.uk/api/jobs/{start}/{end}/{uprn}",
}

ICON_MAP = {
    "Empty Bin 240L Black": "mdi:trash-can",
    "Empty Bin 240L Green": "mdi:recycle",
    "Empty Bin 240L Brown": "mdi:leaf",
}

#_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, post_code=None, number=None, name=None, uprn=None):
        self._post_code = post_code
        self._number = number
        self._name = name
        self._uprn = uprn

    def fetch(self):
        now = datetime.datetime.now().date()
        if not self._uprn:
            # look up the UPRN for the address
            q = str(API_URLS["address_search"]).format(postcode=self._post_code)
            r = requests.get(q)
            r.raise_for_status()
            addresses = r.json()["premises"]

            if self._name:
                self._uprn = [
                    x["uprn"] for x in addresses if x["address"]["address1"].capitalize() == self._name.capitalize()
                ][0]
            elif self._number:
                self._uprn = [
                    x["uprn"] for x in addresses if x["address"]["address2"] == str(self._number)
                ][0]

            if not self._uprn:
                raise Exception(f"Could not find address {self._post_code} {self._number}{self._name}")

        q = str(API_URLS["collection"]).format(
                start=now,
                end=(now + datetime.timedelta(14)),
                uprn=self._uprn
            )
        r = requests.get(q)
        r.raise_for_status()

        collections = r.json()["jobs_FeatureScheduleDates"]
        entries = []

        for collection in collections:
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(
                        collection["nextDate"], "%Y-%m-%dT%H:%M:%S"
                    ).date(),
                    t=collection["jobDescription"],
                    icon=ICON_MAP.get(collection["jobDescription"]),
                )
            )

        return entries
