from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Melton City Council"
DESCRIPTION = "Source for Melton City Council rubbish collection."
URL = "https://www.melton.vic.gov.au"
TEST_CASES = {
    "Tuesday A": {"street_address": "23 PILBARA AVENUE BURNSIDE 3023"},
    "Tuesday B": {"street_address": "29 COROWA CRESCENT BURNSIDE 3023"},
    "Wednesday A": {"street_address": "2 ASPIRE BOULEVARD FRASER RISE 3336"},
    "Wednesday B": {"street_address": "17 KEYNES CIRCUIT FRASER RISE 3336"},
}

ICON_MAP = {
    "Food and Green Waste": Icons.BIO_KITCHEN,
    "Hard Waste": Icons.BULKY,
    "Recycling": Icons.RECYCLING,
}

HEADERS = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "}

_CONFIG = OpenCitiesConfig(
    domain="https://www.melton.vic.gov.au",
    argument_name="street_address",
    headers=HEADERS,
    warm_up_url="https://www.melton.vic.gov.au/My-Area",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
