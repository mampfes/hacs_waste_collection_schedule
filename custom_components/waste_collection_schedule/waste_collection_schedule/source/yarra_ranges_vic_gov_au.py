import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Yarra Ranges Council"
DESCRIPTION = "Source for Yarra Ranges Council rubbish collection."
URL = "https://www.yarraranges.vic.gov.au"
TEST_CASES = {
    "Petstock Lilydale": {"street_address": "447-449 Maroondah Hwy, Lilydale VIC 3140"},
    "Beechworth Bakery Healesville": {
        "street_address": "316 Maroondah Hwy, Healesville VIC 3777"
    },
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "New weekly FOGO collection": "mdi:leaf",
    "Rubbish Collection": "mdi:sofa",
    "Recycling Collection": "mdi:recycle",
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        session = requests.Session()

        response = session.get(
            "https://www.yarraranges.vic.gov.au/Environment/Waste/Find-your-waste-collection-and-burning-off-dates"
        )
        response.raise_for_status()

        response = session.get(
            "https://www.yarraranges.vic.gov.au/api/v1/myarea/search",
            params={"keywords": self._street_address},
        )
        response.raise_for_status()
        addressSearchApiResults = response.json()
        if (
            addressSearchApiResults["Items"] is None
            or len(addressSearchApiResults["Items"]) < 1
        ):
            raise Exception(
                f"Address search for '{self._street_address}' returned no results. Check your address on https://www.yarraranges.vic.gov.au/Environment/Waste/Find-your-waste-collection-and-burning-off-dates"
            )

        addressSearchTopHit = addressSearchApiResults["Items"][0]
        _LOGGER.debug("Address search top hit: %s", addressSearchTopHit)

        geolocationid = addressSearchTopHit["Id"]
        _LOGGER.debug("Geolocationid: %s", geolocationid)

        response = session.get(
            "https://www.yarraranges.vic.gov.au/ocapi/Public/myarea/wasteservices",
            params={"geolocationid": geolocationid, "ocsvclang": "en-AU"},
        )
        response.raise_for_status()

        wasteApiResult = response.json()
        _LOGGER.debug("Waste API result: %s", wasteApiResult)

        soup = BeautifulSoup(wasteApiResult["responseContent"], "html.parser")

        entries = []
        for article in soup.find_all("article"):
            waste_type = article.h3.string
            icon = ICON_MAP.get(waste_type)

            if waste_type == "Burning off":
                continue

            next_pickup = article.find(class_="next-service").string.strip()

            if not re.match(r"[^\s]* \d{1,2}\/\d{1,2}\/\d{4}", next_pickup):
                continue

            next_pickup_date = datetime.strptime(
                next_pickup.split(sep=" ")[1], "%d/%m/%Y"
            ).date()

            if next_pickup_date is None or waste_type is None:
                continue

            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
