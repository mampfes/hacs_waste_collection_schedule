from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Mansfield Shire Council"
DESCRIPTION = "Source for Mansfield Shire Council rubbish collection."
URL = "https://www.mansfield.vic.gov.au"
TEST_CASES = {
    "Delatite Hotel": {"street_address": "95 High Street, Mansfield"},
    "Mansfield Zoo": {"street_address": "1064 Mansfield-Woods Point Road, Mansfield"},
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.mansfield.vic.gov.au",
    argument_name="street_address",
    warm_up_url="https://www.mansfield.vic.gov.au/Community/Residents/Waste-Recycling/Check-My-Bin-Day",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
