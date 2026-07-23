from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Yarra Ranges Council"
DESCRIPTION = "Source for Yarra Ranges Council rubbish collection."
URL = "https://www.yarraranges.vic.gov.au"
TEST_CASES = {
    "Petstock Lilydale": {
        "street_address": "5/447-449 Maroondah Highway Lilydale 3140"
    },
    "Beechworth Bakery Healesville": {
        "street_address": "316 Maroondah Highway Healesville 3777"
    },
}

ICON_MAP = {
    "New weekly FOGO collection": Icons.BIO_KITCHEN,
    "Rubbish Collection": Icons.GENERAL_WASTE,
    "Recycling Collection": Icons.RECYCLING,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.yarraranges.vic.gov.au",
    argument_name="street_address",
    warm_up_url="https://www.yarraranges.vic.gov.au/Environment/Waste/Find-your-waste-collection-and-burning-off-dates",
    icon_keywords=ICON_MAP,
    exclude_types=("Burning off",),
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
