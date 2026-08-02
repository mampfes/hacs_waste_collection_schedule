from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Stonnington City Council"
DESCRIPTION = "Source for Stonnington City Council rubbish collection."
URL = "https://www.stonnington.vic.gov.au"
TEST_CASES = {
    "The Jam Factory": {"street_address": "500 Chapel Street, South Yarra"},
    "Malvern Library": {"street_address": "1255 High Street, Malvern"},
}

ICON_MAP = {
    "Food and Green Waste": Icons.BIO_KITCHEN,
    "Hard Waste": Icons.BULKY,
    "Recycling": Icons.RECYCLING,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.stonnington.vic.gov.au",
    argument_name="street_address",
    warm_up_url="https://www.stonnington.vic.gov.au/Services/Waste-and-recycling",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
