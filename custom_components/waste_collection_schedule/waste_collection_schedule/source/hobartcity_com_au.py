from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "City of Hobart "
DESCRIPTION = "Source for City of Hobart"
URL = "https://www.hobartcity.com.au"
TEST_CASES = {
    "154 FOREST ROAD, WEST HOBART 7000": {
        "address": "154 FOREST ROAD, WEST HOBART 7000"
    },
    "151 AUGUSTA ROAD, LENAH VALLEY 7008": {
        "address": "151 AUGUSTA ROAD, LENAH VALLEY 7008"
    },
}


ICON_MAP = {
    "rubbish": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
    "fogo": Icons.BIO_KITCHEN,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "The address should exactly match the address autocompleted by the website: https://www.hobartcity.com.au/Residents/Waste-and-recycling/When-is-my-bin-collected",
    }
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.hobartcity.com.au",
    page_link="/$720cfbd8-df7e-4b88-bf92-e218d51ee173$/Residents/Waste-and-recycling/When-is-my-bin-collected",
    icon_keywords=ICON_MAP,
    strict_address_matching=True,
)


class Source:
    def __init__(self, address: str) -> None:
        self._address = address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._address)
