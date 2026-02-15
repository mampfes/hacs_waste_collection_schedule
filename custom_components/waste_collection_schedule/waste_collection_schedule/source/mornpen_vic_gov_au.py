import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Mornington Peninsula Shire Council"
DESCRIPTION = "Source for Mornington Peninsula Shire Council rubbish collection."
URL = "https://www.mornpen.vic.gov.au"
TEST_CASES = {
    "Main Ridge Pony Club": {"street_address": "305 Baldrys Rd Main Ridge VIC 3928"},
    "Laneway Espresso Dromana": {
        "street_address": "167 Point Nepean Rd Dromana VIC 3936"
    },
    "Pt. Leo Estate Merricks": {
        "street_address": "3649 Frankston-Flinders Rd Merricks VIC 3916"
    },
}


_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Green waste bin": "mdi:leaf",
    "Household rubbish bin": "mdi:trash-can",
    "Recycling bin": "mdi:recycle",
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        session = requests.Session()

        response = session.get(
            "https://www.mornpen.vic.gov.au/Your-Property/Rubbish-Recycling/Bins/Find-your-bin-day",
            timeout=30,
        )
        response.raise_for_status()

        response = session.get(
            "https://www.mornpen.vic.gov.au/api/v1/myarea/search",
            params={"keywords": self._street_address},
            timeout=30,
        )
        response.raise_for_status()
        addressSearchApiResults = response.json()

        if (
            addressSearchApiResults["Items"] is None
            or len(addressSearchApiResults["Items"]) < 1
        ):
            raise SourceArgumentException(
                "street_address",
                f"Address search for '{self._street_address}' returned no results. Check your address on https://www.mornpen.vic.gov.au/Your-Property/Rubbish-Recycling/Bins/Find-your-bin-day",
            )

        addressSearchTopHit = addressSearchApiResults["Items"][0]
        _LOGGER.debug("Address search top hit: %s", addressSearchTopHit)

        geolocationid = addressSearchTopHit["Id"]
        _LOGGER.debug("Geolocationid: %s", geolocationid)

        response = session.get(
            "https://www.mornpen.vic.gov.au/ocapi/Public/myarea/wasteservices",
            params={"geolocationid": geolocationid, "ocsvclang": "en-AU"},
            timeout=30,
        )
        response.raise_for_status()

        wasteApiResult = response.json()
        _LOGGER.debug("Waste API result: %s", wasteApiResult)

        soup = BeautifulSoup(wasteApiResult["responseContent"], "html.parser")

        entries = []
        for article in soup.find_all("article"):
            if article.h3 is None:
                continue
            waste_type = article.h3.string

            if waste_type is None or waste_type == "Burning off":
                continue

            icon = ICON_MAP.get(waste_type, "mdi:trash-can-outline")

            next_service_div = article.find("div", {"class": "next-service"})
            if next_service_div is None:
                continue
            next_pickup = next_service_div.get_text().strip()

            if not re.match(r"[^\s]* \d{1,2}\/\d{1,2}\/\d{4}", next_pickup):
                continue

            next_pickup_date = datetime.strptime(
                next_pickup.split(sep=" ")[1], "%d/%m/%Y"
            ).date()

            if next_pickup_date is None or waste_type is None:
                continue

            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
