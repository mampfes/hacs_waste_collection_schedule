import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Maroondah City Council"
DESCRIPTION = "Source for Maroondah City Council. Finds both green waste and general recycling dates."
URL = "https://www.maroondah.vic.gov.au"
TEST_CASES = {
    "Monday - Area A": {"address": "1 Abbey Court, RINGWOOD 3134"},  # Monday - Area A
    "Monday - Area B": {
        "address": "1 Angelica Crescent, CROYDON HILLS 3136"
    },  # Monday - Area B
    "Tuesday - Area B": {"address": "6 Como Close, CROYDON 3136"},  # Tuesday - Area B
    "Wednesday - Area A": {
        "address": "113 Dublin Road, RINGWOOD EAST 3135"
    },  # Wednesday - Area A
    "Wednesday - Area B": {
        "address": "282 Maroondah Highway, RINGWOOD 3134"
    },  # Wednesday - Area B
    "Thursday - Area A": {
        "address": "4 Albury Court, CROYDON NORTH 3136"
    },  # Thursday - Area A
    "Thursday - Area B": {
        "address": "54 Lincoln Road, CROYDON 3136"
    },  # Thursday - Area B
    "Friday - Area A": {
        "address": "6 Lionel Crescent, CROYDON 3136"
    },  # Friday - Area A
    "Friday - Area B": {"address": "61 Timms Avenue, KILSYTH 3137"},  # Friday - Area B
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Food and Garden organics": "mdi:leaf",
    "Hard Waste": "mdi:sofa",
    "Recycling": "mdi:recycle",
}


class Source:
    def __init__(self, address):
        self._street_address = address

    def fetch(self):
        session = requests.Session()

        response = session.get(
            "https://www.maroondah.vic.gov.au/Residents-property/Waste-rubbish/Waste-collection-schedule"
        )
        response.raise_for_status()

        response = session.get(
            "https://www.maroondah.vic.gov.au/api/v1/myarea/search",
            params={"keywords": self._street_address},
        )
        response.raise_for_status()
        addressSearchApiResults = response.json()
        if (
            addressSearchApiResults["Items"] is None
            or len(addressSearchApiResults["Items"]) < 1
        ):
            raise Exception(
                f"Address search for '{self._street_address}' returned no results. Check your address on https://www.maroondah.vic.gov.au/Residents-property/Waste-rubbish/Waste-collection-schedule"
            )

        addressSearchTopHit = addressSearchApiResults["Items"][0]
        _LOGGER.debug("Address search top hit: %s", addressSearchTopHit)

        geolocationid = addressSearchTopHit["Id"]
        _LOGGER.debug("Geolocationid: %s", geolocationid)

        response = session.get(
            "https://www.maroondah.vic.gov.au/ocapi/Public/myarea/wasteservices?ocsvclang=en-AU",
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
