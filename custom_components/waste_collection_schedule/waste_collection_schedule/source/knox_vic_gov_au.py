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

class WasteType:
    def __init__(self, name, icon, display_name):
        self.name = name
        self.icon = icon
        self.display_name = display_name

# Define waste types
waste_types = {
    "green": WasteType("green", "mdi:leaf", "Food and garden"),
    "rubbish": WasteType("rubbish", "mdi:trash-can", "Rubbish"),
    "recycling": WasteType("recycling", "mdi:recycle", "Recycling"),
}

class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):

        def extract_date(date_str):
            date_str = date_str.replace("<span>", "")
            date_str = date_str.replace("</span>", "")
            date_str = date_str.replace("Next collection is ", "")
            date_obj = datetime.strptime(date_str, "%d %B %Y").date()
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

        dateString = "_date"
        for key, value in rubbishCollectionApiResult.items():
            if key.endswith(dateString):        
                name = key.replace(dateString, "")
                waste_type = waste_types[name].display_name
                date = extract_date(value)
                icon = waste_types[name].icon
                entries.append(Collection(date=date, t=waste_type, icon=icon))
            
        return entries