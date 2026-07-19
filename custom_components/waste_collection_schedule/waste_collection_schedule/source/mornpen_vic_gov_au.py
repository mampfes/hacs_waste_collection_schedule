from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Mornington Peninsula Shire Council"
DESCRIPTION = "Source for Mornington Peninsula Shire Council rubbish collection."
URL = "https://www.mornpen.vic.gov.au"
TEST_CASES = {
    "Main Ridge Pony Club": {"street_address": "305 Baldrys Rd Main Ridge VIC 3928"},
    "Laneway Espresso Dromana": {
        "street_address": "167 Point Nepean Rd Dromana VIC 3936"
    },
    "Pt. Leo Estate Merricks": {
        "street_address": "3649 Frankston-Flinders Rd Merricks VIC 3916"
    },
}

ICON_MAP = {
    "Green waste bin": Icons.GARDEN,
    "Household rubbish bin": Icons.GENERAL_WASTE,
    "Recycling bin": Icons.RECYCLING,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.mornpen.vic.gov.au",
    argument_name="street_address",
    warm_up_url="https://www.mornpen.vic.gov.au/Your-Property/Rubbish-Recycling/Bins/Find-your-bin-day",
    icon_keywords=ICON_MAP,
    exclude_types=("Burning off",),
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
