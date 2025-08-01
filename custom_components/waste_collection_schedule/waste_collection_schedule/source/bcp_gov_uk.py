import logging
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection

_LOGGER = logging.getLogger(__name__)

TITLE = "BCP Council"
DESCRIPTION = "Bin collection data for Bournemouth, Christchurch and Poole Council, UK"
URL = "https://bcpportal.bcpcouncil.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": 10013449141},
    "Test_002": {"uprn": "10001085438"},
    "Test_003": {"uprn": "100040567667"},
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Rubbish": "mdi:trash-can",
    "Garden Waste": "mdi:leaf",
    "Food Waste": "mdi:food",
}

API_URL = "https://bcpportal.bcpcouncil.gov.uk/checkyourbincollection/"

API_URL_REGEX = re.compile(
    r'function fetchBinCollectionData.*?const response = await fetch\("(.*?)"',
    re.MULTILINE | re.DOTALL,
)


class Source:
    """Fetches bin collection data for BCP Council using the Logic App endpoint."""

    def __init__(self, uprn: str):
        self._uprn = uprn

    def fetch(self):
        r = requests.get(API_URL)
        r.raise_for_status()

        api_url = API_URL_REGEX.search(r.text)
        if not api_url:
            raise ValueError("Could not find API URL in the response.")
        api_url = api_url.group(1)

        _LOGGER.debug("Requesting bin data for UPRN: %s", self._uprn)
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-BCP/1.0",
        }

        payload = {"uprn": self._uprn}

        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(
                f"BCP API request failed: {e} (status: {response.status_code})"
            ) from e

        bin_data = response.json().get("data", [])
        if not bin_data:
            _LOGGER.warning("No collection data returned for UPRN %s", self._uprn)

        entries = []

        for bin in bin_data:
            bin_type = bin.get("wasteContainerUsageTypeDescription", "Unknown")
            date_list = bin.get("scheduleDateRange", [])
            icon = ICON_MAP.get(bin_type, "mdi:delete-empty")

            for date_str in date_list:
                try:
                    collection_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    entries.append(
                        Collection(date=collection_date, t=bin_type, icon=icon)
                    )
                except ValueError:
                    _LOGGER.error("Invalid date format: %s", date_str)

        return entries
