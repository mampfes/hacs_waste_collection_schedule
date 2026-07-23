from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Cassowary Coast Regional Council"
DESCRIPTION = (
    "Source for Cassowary Coast Regional Council, Far North Queensland, Australia."
)
URL = "https://www.cassowarycoast.qld.gov.au"
COUNTRY = "au"
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the full service address used by Cassowary Coast Regional Council, "
        "for example '10 Bombala Street, Mourilyan, 4858'."
    )
}
TEST_CASES = {
    "10 Bombala Street, Mourilyan": {"address": "10 Bombala Street, Mourilyan, 4858"},
}

PAGE_LINK = "/Waste-Water-and-Roads/Waste-and-Recycling/Kerbside-Collection"

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "referer": URL + PAGE_LINK,
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
}

ICON_MAP = {
    "general waste": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your full street address including suburb, e.g. '10 Bombala Street, Mourilyan, 4858'",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Full Street Address",
    },
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.cassowarycoast.qld.gov.au",
    search_fuzzy=True,
    max_results=1,
    page_link=PAGE_LINK,
    headers=HEADERS,
    use_curl_cffi=True,
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, address: str):
        self._address = " ".join(address.split())
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._address)
