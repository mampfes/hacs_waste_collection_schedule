from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Ballina Shire Council"
DESCRIPTION = "Source for Ballina Shire Council, NSW, Australia."
URL = "https://www.ballina.nsw.gov.au/Residents/Waste-and-Recycling/Bin-Collection-Day"
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the full service address used by Ballina Shire Council, for example "
        "'1 Grant St, Ballina NSW 2478'."
    )
}
TEST_CASES = {
    "1 Grant St, Ballina NSW 2478": {"address": "1 Grant St, Ballina NSW 2478"}
}

PAGE_LINK = "/$8a878053-5e29-431d-896b-8c79ce08799f$/Residents/Waste-and-Recycling/Bin-Collection-Day"

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "referer": URL,
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
}

ICON_MAP = {
    "general waste": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
    "green organics": Icons.ORGANIC,
    "food organics": Icons.BIO_KITCHEN,
    "garden organics": Icons.GARDEN,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.ballina.nsw.gov.au",
    search_fuzzy=True,
    max_results=1,
    page_link=PAGE_LINK,
    headers=HEADERS,
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, address: str):
        self._address = " ".join(address.split())
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._address)
