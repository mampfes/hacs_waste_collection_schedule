from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Macedon Ranges Shire Council"
DESCRIPTION = "Source for Macedon Ranges Shire Council rubbish collection."
URL = "https://www.mrsc.vic.gov.au"
TEST_CASES = {
    "Macedon IGA": {"street_address": "20 Victoria Street, Macedon"},
    "ALDI Gisborne": {"street_address": "45 Aitken Street, Gisborne"},
}

ICON_MAP = {
    "FOGO bin": Icons.BIO_KITCHEN,
    "Recycling bin": Icons.RECYCLING,
    "Glass-only bin": Icons.GLASS,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.mrsc.vic.gov.au",
    argument_name="street_address",
    warm_up_url="https://www.mrsc.vic.gov.au/Live-Work/Bins-Rubbish-Recycling/Bins-and-collection-days/Bin-collection-days",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
