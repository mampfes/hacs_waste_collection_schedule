import logging

import requests
from dateutil import parser
from waste_collection_schedule import Collection

TITLE = "Sheffield City Council"
DESCRIPTION = "Source for waste collection services from Sheffield City Council (SCC)"
URL = "https://sheffield.gov.uk/"
TEST_CASES = {
    # These are random addresses around Sheffield
    # If your property is listed here and you don't want it, please raise an issue and I'll amend
    "test001": {"uprn": 100050938234},
    "test002": {"uprn": 100050961380},
    "test003": {"uprn": "100050920796"},
    "test004": {"uprn": "100051085306"},
}


API_URL = "https://wasteservices.sheffield.gov.uk/"

# Headers to mimic the browser
HEADERS = {
    "user-agent": "Mozilla/5.0",
    "Content-type": "application/json",
}

# Icons for the different bin types
ICON_MAP = {
    "BLACK": "mdi:delete-empty",  # General Waste
    "BROWN": "mdi:glass-fragile",  # Glass, Tins, Cans & Plastics
    "BLUE": "mdi:newspaper",  # Paper & Cardboard
    "GREEN": "mdi:leaf",  # Garden Waste
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn=None):
        self._uprn = str(uprn)

    def fetch(self):
        if self._uprn:
            payload = {"councilId": "1", "uprn": f"{self._uprn}"}

            response = requests.post(f"{API_URL}api/getCalendarData", json=payload)
            response.raise_for_status()
            json_doc = response.json()

            if "data" not in json_doc:
                raise ValueError(
                    "The returned API data does not contain expected data element"
                )
            if "message" in json_doc and json_doc["message"] != "OK":
                raise ValueError(f"API advised error: {json_doc['message']}")

            entries = []
            for data_item in json_doc["data"]:
                if "records" not in data_item:
                    continue
                for record in data_item["records"]:
                    collection_date = parser.parse(
                        record["actual_scheduled_date"]
                    ).date()
                    collection_icon = ICON_MAP.get(
                        record["service"].replace(" Bin", "").upper()
                    )
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=record["service"],
                            icon=collection_icon,
                        )
                    )
            return entries
        raise ValueError("No result information found when collected, recheck UPN")
