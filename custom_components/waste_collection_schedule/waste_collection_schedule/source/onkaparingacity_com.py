from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "City of Onkaparinga Council"
DESCRIPTION = "Source for City of Onkaparinga Council, Australia."
URL = "https://www.onkaparingacity.com/"
COUNTRY = "au"
TEST_CASES = {
    "TestcaseI": {"address": "18 Flagstaff Road, FLAGSTAFF HILL 5159"},
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling Waste": Icons.RECYCLING,
    "Green Waste": Icons.GARDEN,
}

HEADERS = {
    "referer": "https://www.onkaparingacity.com/Services/Waste-and-recycling/Bin-collections"
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.onkaparingacity.com",
    headers=HEADERS,
    icon_keywords=ICON_MAP,
    exclude_type_prefixes=("Calendar",),
)


class Source:
    def __init__(self, address: str):
        self._address = address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._address)
