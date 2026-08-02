from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Lane Cove Council"
DESCRIPTION = "Source for Lane Cove Council rubbish collection."
URL = "https://www.lanecove.nsw.gov.au/"

TEST_CASES = {
    "17 Moore ST": {"address": "17 Moore ST LANE COVE WEST, 2066"},
    "1 Austin St": {"address": "1 Austin ST LANE COVE, 2066"},
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Food Waste": Icons.BIO_KITCHEN,
    "Green Waste": Icons.GARDEN,
    "Container Recycling": Icons.RECYCLING,
    "Paper and Cardboard Recycling": Icons.PAPER,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit the Lane Cove Council website and search for your address. "
    "Use the exact address shown in the autocomplete result.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including suburb and postal code",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/plain, */*; q=0.01",
    "Referer": "https://www.lanecove.nsw.gov.au/Services/Waste-and-Recycling/Waste-Collection-Calendar",
    "X-Requested-With": "XMLHttpRequest",
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.lanecove.nsw.gov.au",
    headers=HEADERS,
    icon_keywords=ICON_MAP,
    use_curl_cffi=True,
)


class Source:
    def __init__(self, address: str):
        self._address = address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._address)
