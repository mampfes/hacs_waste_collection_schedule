import json
import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Canterbury City Council"
DESCRIPTION = "Source for canterbury.gov.uk services for canterbury"
URL = "https://canterbury.gov.uk"
TEST_CASES = {
    "houseNumber": {"post_code": "ct68ru", "number": "63"},
    "houseName": {"post_code": "ct68ru", "number": "KOWLOON"},
}
HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://www.canterbury.gov.uk",
    "Referer": "https://www.canterbury.gov.uk/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
    "Accept": "*/*",
}

API_URLS = {
    "address_search": "https://trsewmllv7.execute-api.eu-west-2.amazonaws.com/dev/address",
    "collection": "https://zbr7r13ke2.execute-api.eu-west-2.amazonaws.com/Beta/get-bin-dates",
}

ICON_MAP = {
    "General": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food": "mdi:food-apple",
    "Garden": "mdi:shovel",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, post_code: str, number: str):
        self._post_code = post_code
        self._number = str(number).capitalize()

    def fetch(self):
        # fetch location id
        r = requests.get(
            API_URLS["address_search"],
            params={"postcode": self._post_code, "type": "standard"},
        )
        r.raise_for_status()
        addresses = r.json()

        address_ids = [
            x
            for x in addresses["results"]
            if (
                x["LPI"].get("PAO_TEXT")
                and x["LPI"]["PAO_TEXT"].lower() == self._number.lower()
            )
            or (
                x["LPI"].get("PAO_START_NUMBER")
                and x["LPI"]["PAO_START_NUMBER"].lower() == self._number.lower()
            )
        ]

        if len(address_ids) == 0:
            if len(addresses["results"]) == 0:
                raise SourceArgumentNotFound("post_code", self._post_code)
            raise SourceArgumentNotFoundWithSuggestions(
                "number",
                self._number,
                {
                    x["LPI"].get("PAO_TEXT") or x["LPI"].get("PAO_START_NUMBER")
                    for x in addresses["results"]
                }
                - {None},
            )

        q = str(API_URLS["collection"])
        r = requests.post(
            q,
            json={
                "uprn": address_ids[0]["LPI"]["UPRN"],
                "usrn": address_ids[0]["LPI"]["USRN"],                
            },
            headers=HEADERS,
        )
        r.raise_for_status()

        collectionsRaw = json.loads(r.json()["dates"])
        collections = {
            "General": collectionsRaw["blackBinDay"],
            "Recycling": collectionsRaw["recyclingBinDay"],
            "Food": collectionsRaw["foodBinDay"],
            "Garden": collectionsRaw["gardenBinDay"],
        }
        entries = []

        for collection in collections:
            if len(collections[collection]) <= 0:
                continue
            for date in collections[collection]:
                entries.append(
                    Collection(
                        date=datetime.strptime(date, "%Y-%m-%dT%H:%M:%S").date(),
                        t=collection,
                        icon=ICON_MAP.get(collection),
                    )
                )

        return entries
