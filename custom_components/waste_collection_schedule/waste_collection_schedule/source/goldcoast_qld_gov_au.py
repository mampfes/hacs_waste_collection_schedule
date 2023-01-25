import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Gold Coast City Council"
DESCRIPTION = "Source for Gold Coast Council rubbish collection."
URL = "https://www.goldcoast.qld.gov.au"
TEST_CASES = {
    "MovieWorx": {"street_address": "50 Millaroo Dr Helensvale"},
    "The Henchman": {"street_address": "6/8 Henchman Ave Miami"},
    "Pie Pie": {"street_address": "1887 Gold Coast Hwy Burleigh Heads"},
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {  # Dict of waste types and suitable mdi icons
    "General waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green organics": "mdi:leaf",
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        session = requests.Session()

        # Making a get request
        response = session.get(
            "https://www.goldcoast.qld.gov.au/api/v1/myarea/searchfuzzy?maxresults=1",
            params={"keywords": self._street_address},
        )
        response.raise_for_status()
        addressSearchApiResults = response.json()
        if (
            addressSearchApiResults["Items"] is None
            or len(addressSearchApiResults["Items"]) < 1
        ):
            raise Exception(
                f"Address search for '{self._street_address}' returned no results. Check your address on https://www.goldcoast.qld.gov.au/Services/Waste-recycling/Find-my-bin-day"
            )

        addressSearchTopHit = addressSearchApiResults["Items"][0]
        _LOGGER.debug("Address search top hit: %s", addressSearchTopHit)

        geolocationid = addressSearchTopHit["Id"]
        _LOGGER.debug("Geolocationid: %s", geolocationid)

        response = session.get(
            "Https://www.goldcoast.qld.gov.au/ocapi/Public/myarea/wasteservices?ocsvclang=en-AU",
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
            if re.match(r"[^\s]* \d{1,2}\/\d{1,2}\/\d{4}", next_pickup):
                next_pickup_date = datetime.strptime(
                    next_pickup.split(sep=" ")[1], "%d/%m/%Y"
                ).date()
                entries.append(
                    Collection(date=next_pickup_date, t=waste_type, icon=icon)
                )

        return entries
