from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Rural City of Wangaratta"
DESCRIPTION = "Source for Rural City of Wangaratta rubbish collection."
URL = "https://www.wangaratta.vic.gov.au"
TEST_CASES = {
    "Wangaratta High School": {"street_address": "Edwards Street WANGARATTA VIC 3677"},
    "KFC Wangaratta": {"street_address": "23-27 Ryley Street WANGARATTA VIC 3677"},
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Organics": Icons.ORGANIC,
    "Recycling": Icons.RECYCLING,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.wangaratta.vic.gov.au",
    argument_name="street_address",
    warm_up_url="https://www.wangaratta.vic.gov.au/Services/Waste-Recycling/Kerbside-Collection/Check-your-bin-day",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
