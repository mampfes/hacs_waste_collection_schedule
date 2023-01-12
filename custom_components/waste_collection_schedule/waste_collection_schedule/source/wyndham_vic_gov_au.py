import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wyndham City Council, Melbourne"
DESCRIPTION = "Source for Wyndham City Council rubbish collection."
URL = "https://wyndham.vic.gov.au"
TEST_CASES = {
    "Truganina South Primary School": {
        "street_address": "3-19 Parkvista Drive TRUGANINA 3029"
    },
    "Westbourne Grammar School": {"street_address": "300 Sayers Road TRUGANINA 3029"},
    "Werribee Mercy Hospital": {
        "street_address": "300-310 Princes Highway WERRIBEE 3030"
    },
    "Wyndham Park Primary School": {
        "street_address": "59-77 Kookaburra Avenue WERRIBEE 3030"
    },
}

API_URL = "https://digital.wyndham.vic.gov.au/myWyndham/"
ICON_MAP = {
    "Green Waste": "mdi:leaf",
    "Garbage": "mdi:trash-can-outline",
    "Recycling": "mdi:recycle",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        session = requests.Session()
        response = session.get(API_URL)
        response.raise_for_status()
        response = session.get(
            "https://digital.wyndham.vic.gov.au/myWyndham/ajax/address-search-suggestions.asp?",
            params=dict(ASEARCH=self._street_address),
        )
        response.raise_for_status()
        html = response.content
        property_address = BeautifulSoup(html, "html.parser").find("li").get_text()
        _LOGGER.debug("Fetched Property Address: %s", property_address)
        if (
            property_address == "No match found."
            or property_address.upper() != self._street_address.upper()
        ):
            raise Exception(
                f"Address search for '{self._street_address}' returned no results. Check your address on "
                f"https://digital.wyndham.vic.gov.au/myWyndham/ "
            )

        property_number = BeautifulSoup(html, "html.parser").find("span").get_text()
        _LOGGER.debug("Fetched Property Number: %s", property_number)
        response = session.get(
            "https://digital.wyndham.vic.gov.au/myWyndham/init-map-data.asp",
            params=dict(
                propnum=property_number, radius="1000", mapfeatures="23,37,22,33,35"
            ),
        )
        response.raise_for_status()
        wasteApiResult = response.content
        soup = BeautifulSoup(wasteApiResult, "html.parser")
        entries = []

        for article in soup.findAll("div", {"class": "waste"}):
            if article.get_text().startswith("Next"):
                waste_type = (
                    article.get_text()
                    .strip()
                    .split(":")[0][5:]
                    .replace(" Collection", "")
                )
                _LOGGER.debug("Waste Type: %s", waste_type)
                icon = ICON_MAP.get(waste_type)
                _LOGGER.debug("Icon: %s", icon)
                next_pickup_date = datetime.strptime(
                    article.get_text().split(":")[1].strip(), "%A, %d %B %Y"
                ).date()
                _LOGGER.debug("Next Pickup Date: %s", next_pickup_date)
                entries.append(
                    Collection(date=next_pickup_date, t=waste_type, icon=icon)
                )
        return entries
