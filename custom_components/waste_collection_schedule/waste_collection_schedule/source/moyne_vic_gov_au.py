from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Moyne Shire Council"
DESCRIPTION = "Source for Moyne Shire Council rubbish collection."
URL = "https://www.moyne.vic.gov.au"
TEST_CASES = {"Test": {"street_address": "1 Cox Street, PORT FAIRY, 3284"}}

ICON_MAP = {
    "Landfill": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "FOGO": Icons.BIO_KITCHEN,
    "Glass Only": Icons.GLASS,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.moyne.vic.gov.au",
    argument_name="street_address",
    warm_up_url="https://www.moyne.vic.gov.au/Your-property/Waste-and-recycling/Kerbside-collection-dates",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
