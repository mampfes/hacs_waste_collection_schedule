import logging
from datetime import datetime
from urllib.parse import quote as urlquote

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Tewkesbury Borough Council"
DESCRIPTION = "Home waste collection schedule for Tewkesbury Borough Council"
URL = "https://www.tewkesbury.gov.uk"
TEST_CASES = {
    "UPRN example": {"uprn": 100120544973},
    "Deprecated postcode": {"postcode": "GL20 5TT"},
    "Deprecated postcode No Spaces": {"postcode": "GL205TT"},
}

DEPRICATED_API_URL = "https://api-2.tewkesbury.gov.uk/general/rounds/%s/nextCollection"
API_URL = "https://api-2.tewkesbury.gov.uk/incab/rounds/%s/next-collection"

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
    "Food": "mdi:silverware-fork-knife",
}

LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, postcode: str | None = None, uprn: str | None = None):
        self.urpn = str(uprn) if uprn is not None else None
        self.postcode = str(postcode) if postcode is not None else None

    def fetch(self):
        if self.urpn is None:
            LOGGER.warning(
                "Using deprecated API might not work in the future. Please provide a UPRN."
            )
            return self.get_data(self.postcode, DEPRICATED_API_URL)
        return self.get_data(self.urpn)

    def get_data(self, uprn, api_url=API_URL):
        if uprn is None:
            raise Exception("UPRN not set")

        encoded_urpn = urlquote(uprn)
        request_url = api_url % encoded_urpn
        response = requests.get(request_url)

        response.raise_for_status()
        data = response.json()

        entries = []

        if data["status"] != "OK":
            raise Exception(
                f"Error fetching data. \"{data['status']}\": \n {data['body']}"
            )

        schedule = data["body"]
        for schedule_entry in schedule:
            entries.append(
                Collection(
                    date=datetime.strptime(
                        schedule_entry["NextCollection"], "%Y-%m-%d"
                    ).date(),
                    t=schedule_entry["collectionType"],
                    icon=ICON_MAP.get(schedule_entry["collectionType"]),
                )
            )

        return entries
