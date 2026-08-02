from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "City of Monash"
DESCRIPTION = "Source for City of Monash rubbish collection."
URL = "https://www.monash.vic.gov.au/"

TEST_CASES = {
    "Test_001": {"address": "4 Carson Street, Mulgrave 3170"},
    "Test_002": {"address": "57 Hamilton Place, Mount Waverley 3149"},
}

SEARCH_PAGE_URL = f"{URL}Waste-Sustainability/Bin-Collection/When-we-collect-your-bins"
ICON_MAP = {
    "Landfill Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Food and Garden Waste": Icons.BIO_KITCHEN,
}

# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": f'Visit the [City of Monash]({SEARCH_PAGE_URL}) "When we collect your bins" page and search for your address. For example: 4 Carson Street, Mulgrave 3170. The arguments should exactly match the full street address after selecting the autocomplete result.',
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including suburb and postal code",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

# ### End of arguments affecting the configuration GUI ####

_CONFIG = OpenCitiesConfig(
    domain=URL.rstrip("/"),
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, address: str):
        self._address = address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._address)
