import logging
from datetime import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = 'Melton City Council'
DESCRIPTION = 'Source for Melton City Council rubbish collection.'
URL = 'https://www.melton.vic.gov.au/My-Area'
TEST_CASES = {
    'Tuesday A': {'street_address': '23 PILBARA AVENUE BURNSIDE 3023'},
    'Tuesday A Geolocation ID': {'geolocation_id': '00faf1f7-9aa0-4b2c-a9b9-54c29401e68c'},
    'Tuesday B': {'street_address': '29 COROWA CRESCENT BURNSIDE 3023'},
    'Wednesday A': {'street_address': '2 ASPIRE BOULEVARD FRASER RISE 3336'},
    'Wednesday B': {'street_address': '17 KEYNES CIRCUIT FRASER RISE 3336'}
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Food and Green Waste": "mdi:leaf",
    "Hard Waste": "mdi:sofa",
    "Recycling": "mdi:recycle",
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        session = requests.Session()

        response = session.get(
            "https://www.melton.vic.gov.au/My-Area"
        )
        response.raise_for_status()

        response = session.get(
            "https://www.melton.vic.gov.au/api/v1/myarea/search",
            params={"keywords": self._street_address},
        )
        response.raise_for_status()
        addressSearchApiResults = response.json()
        if (
            addressSearchApiResults["Items"] is None
            or len(addressSearchApiResults["Items"]) < 1
        ):
            _LOGGER.error(
                f"Address search for '{self._street_address}' returned no results. Check your address on https://www.melton.vic.gov.au/My-Area"
            )
            return []

        addressSearchTopHit = addressSearchApiResults["Items"][0]
        _LOGGER.debug("Address search top hit: %s", addressSearchTopHit)

        geolocationid = addressSearchTopHit["Id"]
        _LOGGER.debug("Geolocationid: %s", geolocationid)

        response = session.get(
            "https://www.melton.vic.gov.au/ocapi/Public/myarea/wasteservices?ocsvclang=en-AU",
            params={"geolocationid": geolocationid},
        )
        response.raise_for_status()

        wasteApiResult = response.json()
        _LOGGER.debug("Waste API result: %s", wasteApiResult)

        soup = BeautifulSoup(wasteApiResult["responseContent"], "html.parser")

        entries = []
        for article in soup.find_all("article"):
            waste_type = article.h3.string
            icon = ICON_MAP.get(waste_type, "mdi:trash-can")
            next_pickup = article.find(class_="next-service").string.strip()
            if re.match("[^\s]* \d{1,2}\/\d{1,2}\/\d{4}", next_pickup):
                next_pickup_date = datetime.strptime(
                    next_pickup.split(sep=" ")[1], "%d/%m/%Y"
                ).date()
                entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
