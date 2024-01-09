import logging
from datetime import datetime
from urllib.parse import urlencode, urljoin

import requests
from waste_collection_schedule import Collection  # type: ignore

TITLE = "Hobsons Bay City Council"
DESCRIPTION = "Source for Hobsons Bay City Council waste & recycling collection"
URL = "https://www.hobsonsbay.vic.gov.au"
TEST_CASES = {
    "Civic Parade Medical Centre": {"street_address": "399 Queen St, Altona Meadows"},
    "Hecho En Mexico Altona": {"street_address": "48 Pier St, Altona"},
}

API_URL = "https://hbcc-seven.vercel.app/api/"
SEARCH_API_URL = "https://jw7fda7yti-2.algolianet.com/1/indexes/*/queries"
SEARCH_APPLICATION_ID = "JW7FDA7YTI"
SEARCH_API_KEY = "7a3b39eba83ef97796c682e6a749be71"
ICON_MAP = {
    "Rubbish": "mdi:trash-can-outline",
    "Commingled Recycling": "mdi:recycle",
    "Food and Garden": "mdi:leaf",
    "Glass": "mdi:glass-fragile",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def fetch(self):
        _LOGGER.debug(f"Searching for address {self._street_address}")

        search_params = {
            "x-algolia-api-key": SEARCH_API_KEY,
            "x-algolia-application-id": SEARCH_APPLICATION_ID,
        }

        # &query=&tagFilters=

        search_data = {
            "requests": [
                {
                    "indexName": "addresses",
                    "params": urlencode(
                        {
                            "facets": [],
                            "highlightPostTag": "</ais-highlight-0000000000>",
                            "highlightPreTag": "<ais-highlight-0000000000>",
                            "hitsPerPage": 1,  # no point in fetching more without a UI to select
                            "query": self._street_address,
                            "tagFilters": "",
                        }
                    ),
                }
            ]
        }

        search_response = requests.post(
            SEARCH_API_URL, params=search_params, json=search_data
        )

        search_response.raise_for_status()
        match = search_response.json()["results"][0]["hits"][0]

        _LOGGER.debug(f"Search result: {match}")

        asn = match["Assessment Number"]

        _LOGGER.info(f"ASN: {asn}")

        addresses_params = {"asn": asn}
        addresses_endpoint = urljoin(API_URL, "addresses")
        addresses_response = requests.get(addresses_endpoint, params=addresses_params)
        addresses_response.raise_for_status()
        address = addresses_response.json()["rows"][0]

        day = address["day"]
        area = address["area"]

        _LOGGER.debug(f"Address result: {address}")
        _LOGGER.info(f"Day: {day}, Area: {area}")

        schedules_params = {"day": day, "area": area}
        schedules_endpoint = urljoin(API_URL, "schedules")
        schedules_response = requests.get(schedules_endpoint, params=schedules_params)
        schedules_response.raise_for_status()
        schedules = schedules_response.json()["rows"]

        _LOGGER.debug(f"Schedules: {schedules}")

        entries = [
            Collection(
                date=datetime.strptime(s["date"], "%d/%m/%Y").date(),
                t=s["bin_type"],
                icon=ICON_MAP.get(s["bin_type"], "Rubbish"),
            )
            for s in schedules
        ]

        return entries
