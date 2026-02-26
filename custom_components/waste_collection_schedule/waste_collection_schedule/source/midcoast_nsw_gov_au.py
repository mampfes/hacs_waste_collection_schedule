import logging
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "MidCoast Council"
DESCRIPTION = "Source for MidCoast Council (NSW) rubbish collection."
URL = "https://www.midcoast.nsw.gov.au/"
DEEPLINK = f"{URL}Services/Waste-and-recycling/When-is-my-bin-collected"
API_URL = f"{URL}ocapi/Public/myarea/wasteservices?ocsvclang=en-AU"
SEARCH_URL = f"{URL}api/v1/myarea/search"
TEST_CASES = {
    "Randomly Selected Address": {"street_address": "101 Goldens Road, FORSTER"}
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    @staticmethod
    def next_weekday(target_day):
        day_map = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }
        if target_day not in day_map:
            raise ValueError(
                f"Error calculating date for general waste, returned day as {target_day}. Please raise an issue."
            )

        today = datetime.now().date()
        target_weekday = day_map[target_day]
        days_ahead = (target_weekday - today.weekday()) % 7

        return today + timedelta(days=days_ahead)

    def fetch(self):
        session = requests.Session()

        response = session.get(URL, timeout=30)
        response.raise_for_status()

        response = session.get(
            SEARCH_URL,
            params={"keywords": self._street_address},
        )
        response.raise_for_status()
        addressSearchApiResults = response.json()
        if (
            addressSearchApiResults["Items"] is None
            or len(addressSearchApiResults["Items"]) < 1
        ):
            raise ValueError(
                f"Address search for '{self._street_address}' returned no results. Check your address on {DEEPLINK}"
            )

        addressSearchTopHit = addressSearchApiResults["Items"][0]
        _LOGGER.debug("Address search top hit: %s", addressSearchTopHit)

        geolocationid = addressSearchTopHit["Id"]
        _LOGGER.debug("Geolocationid: %s", geolocationid)

        response = session.get(
            API_URL,
            params={"geolocationid": geolocationid},
        )
        response.raise_for_status()

        wasteApiResult = response.json()
        _LOGGER.debug("Waste API result: %s", wasteApiResult)

        soup = BeautifulSoup(wasteApiResult["responseContent"], "html.parser")

        entries = []
        for article in soup.find_all("article"):
            waste_type = article.h3.string.strip()
            if waste_type not in ICON_MAP:
                _LOGGER.debug("Skipping non-waste entry: %s", waste_type)
                continue
            icon = ICON_MAP.get(waste_type, "mdi:trash-can-outline")
            next_pickup = article.find(class_="next-service").string.strip()
            if re.match(r"[^\s]* \d{1,2}\/\d{1,2}\/\d{4}", next_pickup):
                next_pickup_date = datetime.strptime(
                    next_pickup.split(sep=" ")[1], "%d/%m/%Y"
                ).date()
                entries.append(
                    Collection(date=next_pickup_date, t=waste_type, icon=icon)
                )
            elif next_pickup.startswith("Every"):
                day_string = next_pickup.split(sep=" ")[1]
                next_pickup_date = Source.next_weekday(day_string)
                entries.append(
                    Collection(date=next_pickup_date, t=waste_type, icon=icon)
                )

        return entries
