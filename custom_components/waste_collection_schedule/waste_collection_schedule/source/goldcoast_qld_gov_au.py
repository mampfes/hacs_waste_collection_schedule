from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Gold Coast City Council"
DESCRIPTION = "Source for Gold Coast Council rubbish collection."
URL = "https://www.goldcoast.qld.gov.au"
TEST_CASES = {
    "MovieWorx": {"street_address": "50 Millaroo Dr Helensvale"},
    "The Henchman": {"street_address": "6/8 Henchman Ave Miami"},
    "Pie Pie": {"street_address": "1887 Gold Coast Hwy Burleigh Heads"},
}

ICON_MAP = {
    "General waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Green organics": Icons.ORGANIC,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.goldcoast.qld.gov.au",
    argument_name="street_address",
    search_fuzzy=True,
    max_results=1,
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
