import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Macedon Ranges Shire Council"
DESCRIPTION = "Source for Macedon Ranges Shire Council rubbish collection."
URL = "https://www.mrsc.vic.gov.au"
TEST_CASES = {
    "Macedon IGA": {"street_address": "20 Victoria Street, Macedon"},
    "ALDI Gisborne": {"street_address": "45 Aitken Street, Gisborne"},
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "FOGO bin": "mdi:leaf",
    "Recycling bin": "mdi:recycle",
    "Glass-only bin": "mdi:glass-fragile",
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        session = requests.Session()

        response = session.get(
            "https://www.mrsc.vic.gov.au/Live-Work/Bins-Rubbish-Recycling/Bins-and-collection-days/Bin-collection-days"
        )
        response.raise_for_status()

        response = session.get(
            "https://www.mrsc.vic.gov.au/api/v1/myarea/search",
            params={"keywords": self._street_address},
        )
        response.raise_for_status()
        addressSearchApiResults = response.json()
        if (
            addressSearchApiResults["Items"] is None
            or len(addressSearchApiResults["Items"]) < 1
        ):
            raise Exception(
                f"Address search for '{self._street_address}' returned no results. Check your address on https://www.mrsc.vic.gov.au/Live-Work/Bins-Rubbish-Recycling/Bins-and-collection-days/Bin-collection-days"
            )

        addressSearchTopHit = addressSearchApiResults["Items"][0]
        _LOGGER.debug("Address search top hit: %s", addressSearchTopHit)

        geolocationid = addressSearchTopHit["Id"]
        _LOGGER.debug("Geolocationid: %s", geolocationid)

        response = session.get(
            "https://www.mrsc.vic.gov.au/ocapi/Public/myarea/wasteservices?ocsvclang=en-AU",
            params={"geolocationid": geolocationid},
        )
        response.raise_for_status()

        wasteApiResult = response.json()
        _LOGGER.debug("Waste API result: %s", wasteApiResult)

        soup = BeautifulSoup(wasteApiResult["responseContent"], "html.parser")

        entries = []
        for article in soup.find_all("article"):
            waste_type = article.h3.string
            icon = ICON_MAP.get(waste_type)
            next_pickup = article.find(class_="next-service").string.strip()
            if re.match(r"[^\s]* \d{1,2}\/\d{1,2}\/\d{4}", next_pickup):
                next_pickup_date = datetime.strptime(
                    next_pickup.split(sep=" ")[1], "%d/%m/%Y"
                ).date()
                entries.append(
                    Collection(date=next_pickup_date, t=waste_type, icon=icon)
                )

        return entries
