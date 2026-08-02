from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Lake Macquarie City Council"
DESCRIPTION = "Source for Lake Macquarie City Council, Australia."
URL = "https://www.lakemac.com.au/"
TEST_CASES = {
    "TestcaseI": {"address": "te"},
    "TestcaseII": {"address": "386 Pacific Highway, MURRAYS BEACH NSW 2281"},
}

ICON_MAP = {
    "General waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Green waste": Icons.GARDEN,
    "Bulk waste": Icons.GENERAL_WASTE,
}

HEADERS = {
    "referer": "https://www.lakemac.com.au/For-residents/Waste-and-recycling/When-are-your-bins-collected"
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.lakemac.com.au",
    headers=HEADERS,
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, address: str):
        self._address = address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._address)
