import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Breckland Council"
DESCRIPTION = "Source for breckland.gov.uk"
URL = "https://www.breckland.gov.uk/mybreckland"
TEST_CASES = {
    "test1": {"postcode": "IP22 2LJ", "address": "glen travis"},
    "test2": {"uprn": "10011977093"},
}

API_URL = "https://www.breckland.gov.uk/apiserver/ajaxlibrary"
ICON_MAP = {
    "Refuse Collection Service": "mdi:trash-can",
    "Recycling Collection Service": "mdi:recycle",
    "Garden Waste Service": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)

headers = {"referer": URL}


class Source:
    def __init__(self, postcode=None, address=None, uprn=None):
        self._postcode = postcode
        self._address = address
        self._uprn = uprn

        if postcode is None and address is None and uprn is None:
            raise Exception("no attributes - specify postcode and address or just uprn")

    def fetch(self):
        if self._uprn is None:
            json_data = {
                "jsonrpc": "2.0",
                "id": "",
                "method": "Breckland.Whitespace.JointWasteAPI.GetSiteIDsByPostcode",
                "params": {"postcode": self._postcode, "environment": "live"},
            }

            r = requests.post(API_URL, json=json_data, headers=headers)
            r.raise_for_status()

            json_response = r.json()

            for key in json_response["result"]:
                if self._address.lower() in key["name"].lower():
                    self._uprn = key["uprn"]

        if self._uprn is None:
            raise Exception("Error querying calendar data")

        json_data = {
            "jsonrpc": "2.0",
            "id": "",
            "method": "Breckland.Whitespace.JointWasteAPI.GetBinCollectionsByUprn",
            "params": {"uprn": self._uprn, "environment": "live"},
        }

        r = requests.post(API_URL, json=json_data, headers=headers)
        r.raise_for_status()

        waste = r.json()["result"]

        entries = []

        for data in waste:
            entries.append(
                Collection(
                    datetime.strptime(
                        data["nextcollection"], "%d/%m/%Y %H:%M:%S"
                    ).date(),
                    data["collectiontype"],
                    ICON_MAP.get(data["collectiontype"]),
                )
            )

        return entries
