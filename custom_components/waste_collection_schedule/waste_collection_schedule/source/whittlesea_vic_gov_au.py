from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Whittlesea City Council"
DESCRIPTION = "Source for Whittlesea Council (VIC) rubbish collection."
URL = "https://www.whittlesea.vic.gov.au/My-Neighbourhood"
TEST_CASES = {
    "Whittlesea Council Office": {
        "street_address": "25 Ferres Boulevard, South Morang 3752"
    }
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Green Waste": Icons.GARDEN,
    "Glass": Icons.GLASS,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.whittlesea.vic.gov.au",
    argument_name="street_address",
    warm_up_url="https://www.whittlesea.vic.gov.au/My-Neighbourhood",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
