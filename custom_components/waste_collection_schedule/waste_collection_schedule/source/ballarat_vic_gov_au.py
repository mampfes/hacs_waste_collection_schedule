import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Ballarat"
DESCRIPTION = "Source for City of Ballarat rubbish collection."
URL = "https://www.ballarat.vic.gov.au"
TEST_CASES = {
    "Clothesline Cafe": {
        "street_address": "202 Humffray Street South BAKERY HILL VIC 3350"
    },
    "Cuthberts Road Milk Bar": {
        "street_address": "27 Cuthberts Road ALFREDTON VIC 3350"
    },
}

_LOGGER = logging.getLogger(__name__)

WASTE_NAMES = {
    "waste": "General Waste",
    "recycle": "Recycling",
    "green": "Green Waste",
}

ICON_MAP = {
    "waste": "mdi:trash-can",
    "recycle": "mdi:recycle",
    "green": "mdi:leaf",
}


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        session = requests.Session()

        response = session.get(
            "https://data.ballarat.vic.gov.au/api/records/1.0/search/",
            params={"dataset": "waste-collection-days", "q": self._street_address},
        )
        response.raise_for_status()
        addressSearchApiResults = response.json()
        if (
            addressSearchApiResults["records"] is None
            or len(addressSearchApiResults["records"]) < 1
        ):
            raise Exception(
                f"Address search for '{self._street_address}' returned no results. Check your address on https://data.ballarat.vic.gov.au/pages/waste-collection-day/"
            )

        addressSearchTopHit = addressSearchApiResults["records"][0]
        _LOGGER.debug("Address search top hit: %s", addressSearchTopHit)

        entries = []
        collection_dates = [
            (key.replace("next", ""), val)
            for key, val in addressSearchTopHit["fields"].items()
            if key.startswith("next")
        ]
        for collection_type, collection_date in collection_dates:
            date = datetime.strptime(collection_date, "%Y-%m-%d").date()
            entries.append(
                Collection(
                    date=date,
                    t=WASTE_NAMES.get(collection_type, collection_type),
                    icon=ICON_MAP.get(collection_type, "mdi:trash-can"),
                )
            )

        return entries
