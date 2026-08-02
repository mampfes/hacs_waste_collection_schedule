from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Nillumbik Shire Council"
DESCRIPTION = "Source for Nillumbik Shire Council rubbish collection."
URL = "https://www.nillumbik.vic.gov.au"
TEST_CASES = {"Test": {"street_address": "11 Sunnyside Crescent, WATTLE GLEN, 3096"}}

ICON_MAP = {
    "Food and Green Waste": Icons.BIO_KITCHEN,
    "Hard Waste": Icons.BULKY,
    "Recycling": Icons.RECYCLING,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.nillumbik.vic.gov.au",
    argument_name="street_address",
    warm_up_url="https://www.nillumbik.vic.gov.au/Residents/Waste-and-recycling/Bin-collection/Check-my-bin-day",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
