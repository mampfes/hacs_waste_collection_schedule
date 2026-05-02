import logging
from datetime import datetime
from urllib.parse import quote as urlquote

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentRequired

TITLE = "Tewkesbury Borough Council"
DESCRIPTION = "Home waste collection schedule for Tewkesbury Borough Council"
URL = "https://www.tewkesbury.gov.uk"
TEST_CASES = {
    "UPRN example": {"uprn": 100120544973},
    "Deprecated postcode": {"postcode": "GL20 5TT"},
    "Deprecated postcode No Spaces": {"postcode": "GL205TT"},
}

DEPRECATED_API_URL = "https://api-2.tewkesbury.gov.uk/general/rounds/%s/nextCollection"
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
        self.uprn = str(uprn) if uprn is not None else None
        self.postcode = str(postcode) if postcode is not None else None

    def fetch(self):
        if self.uprn is None:
            LOGGER.warning(
                "Using deprecated API might not work in the future. Please provide a UPRN."
            )
            return self.get_data(self.postcode, DEPRECATED_API_URL)
        return self.get_data(self.uprn)

    def get_data(self, uprn, api_url=API_URL):
        if uprn is None:
            raise SourceArgumentRequired("uprn", "UPRN is required to fetch collection data")

        encoded_uprn = urlquote(uprn)
        request_url = api_url % encoded_uprn
        response = requests.get(request_url)

        response.raise_for_status()
        data = response.json()

        entries = []

        waste_type_map = {
            "refuse": "Refuse",
            "recycling": "Recycling",
            "food": "Food",
            "garden": "Garden",
        }
        for waste_key, waste_label in waste_type_map.items():
            if waste_key not in data:
                continue
            date_str = data[waste_key].get("nextCollectionDate")
            if not date_str:
                continue
            entries.append(
                Collection(
                    date=datetime.fromisoformat(date_str.replace("Z", "+00:00")).date(),
                    t=waste_label,
                    icon=ICON_MAP.get(waste_label),
                )
            )
        if not entries:
            raise Exception(f"No collection data returned for identifier: {uprn!r}")
        return entries
