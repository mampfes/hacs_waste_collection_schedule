import logging
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Knox City Council"
DESCRIPTION = "Source for Knox City Council rubbish collection."
URL = "https://www.knox.vic.gov.au/"
TEST_CASES = {
    "Lorna Café": {
        "street_address": "1053 Burwood Highway, FERNTREE GULLY VIC 3156"
    },
    "Country Cob Bakery": {
        "street_address": "951 Mountain Highway, BORONIA VIC 3155"
    },
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Food and garden": "mdi:leaf",
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):

        def extract_date(date_str):
            date_str = date_str.replace('<span>', '')
            date_str = date_str.replace('</span>', '')
            date_str = date_str.replace('Next collection is ', '')
            date_obj = datetime.strptime(date_str, '%d %B %Y').date()
            return date_obj
        
        session = requests.Session()

        response = session.get(
            "https://www.knox.vic.gov.au/our-services/bins-rubbish-and-recycling/find-my-bin-days"
        )
        response.raise_for_status()

        response = session.get(
            "https://www.knox.vic.gov.au/rubbish-collection/autocomplete/find",
            params={"q": self._street_address},
        )
        response.raise_for_status()
        addressSearchApiResults = response.json()
        if not isinstance(addressSearchApiResults, list) or len(addressSearchApiResults) < 1:
            raise Exception(f"Address search for '{self._street_address}' returned no results. Check your address on https://www.knox.vic.gov.au/our-services/bins-rubbish-and-recycling/find-my-bin-days")

        addressSearchTopHit = addressSearchApiResults[0]
        _LOGGER.debug("Address search top hit: %s", addressSearchTopHit)

        geolocationid = addressSearchTopHit["value"]
        _LOGGER.debug("Geolocationid: %s", geolocationid)

        response = session.get(
            "https://www.knox.vic.gov.au/rubbish-collection/find",
            params={"address": geolocationid},
        )
        response.raise_for_status()

        rubbishCollectionApiResult = response.json()
        _LOGGER.debug("Rubblish Collection API result: %s", rubbishCollectionApiResult)

        entries = []

        if 'rubbish_date' in rubbishCollectionApiResult:
            rubbish_date = extract_date(rubbishCollectionApiResult['rubbish_date'])
            name="Rubbish"
            icon=ICON_MAP.get(name)
            entries.append(Collection(date=rubbish_date, t=name, icon=icon))

        if 'recycling_date' in rubbishCollectionApiResult:
            recycling_date = extract_date(rubbishCollectionApiResult['recycling_date'])
            name="Recycling"
            icon=ICON_MAP.get(name)
            entries.append(Collection(date=recycling_date, t=name, icon=icon))

        if 'green_date' in rubbishCollectionApiResult:
            green_date = extract_date(rubbishCollectionApiResult['green_date'])
            name="Food and garden"
            icon=ICON_MAP.get(name)
            entries.append(Collection(date=green_date, t=name, icon=icon))
            
        return entries