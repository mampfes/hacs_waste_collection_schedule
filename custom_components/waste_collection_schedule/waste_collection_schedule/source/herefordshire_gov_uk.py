import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Herefordshire City Council"
DESCRIPTION = "Source for herefordshire.gov.uk services for hereford"
URL = "https://herefordshire.gov.uk"
TEST_CASES = {
    "houseNumber": {"post_code": "hr49js", "number": "40"},
}

API_URLS = {
    "address_search": "https://trsewmllv7.execute-api.eu-west-2.amazonaws.com/dev/address",
    "collection": "https://www.herefordshire.gov.uk/rubbish-recycling/check-bin-collection-day",  # ?blpu_uprn=200002607454",
}

ICON_MAP = {
    "General": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, post_code: str, number: str):
        self._post_code = post_code
        self._number = str(number).capitalize()

    def fetch(self):
        # fetch location id
        r = requests.get(
            API_URLS["address_search"],
            params={"postcode": self._post_code, "type": "standard"},
        )
        r.raise_for_status()
        addresses = r.json()

        address_ids = [
            x
            for x in addresses["results"]
            if (
                x["LPI"].get("PAO_TEXT")
                and x["LPI"]["PAO_TEXT"].lower() == self._number.lower()
            )
            or (
                x["LPI"].get("PAO_START_NUMBER")
                and x["LPI"]["PAO_START_NUMBER"].lower() == self._number.lower()
            )
        ]

        if len(address_ids) == 0:
            raise Exception(f"Could not find address {self._post_code} {self._number}")

        q = str(API_URLS["collection"])
        r = requests.get(q, params={"blpu_uprn": address_ids[0]["LPI"]["UPRN"]})
        r.raise_for_status()

        bs = BeautifulSoup(r.text, "html.parser").find_all(id="wasteCollectionDates")[0]

        entries = [
            Collection(
                date=datetime.strptime(
                    bs.find_all(id="altnextWasteDay")[0].string.strip(), "%A %d %B %Y"
                ).date(),
                t="General rubbish",
                icon="mdi:trash-can",
            ),
            Collection(
                date=datetime.strptime(
                    bs.find_all(id="altnextRecyclingDay")[0].string.strip(),
                    "%A %d %B %Y",
                ).date(),
                t="Recycling",
                icon="mdi:recycle",
            ),
        ]

        return entries
