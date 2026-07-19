from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Logan City Council"
DESCRIPTION = "Source for Logan City Council rubbish collection."
URL = "https://www.logan.qld.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "Lee Naki's Takeaway": {"property_location": "12 Ashton Street Kingston"},
    "LCC Administration Centre": {
        "property_location": "150 Wembley Road Logan Central"
    },
    "Rochedale South (with green waste)": {
        "property_location": "53 Wendron Street Rochedale South"
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your street address as used on the Logan City Council MyLogan tool "
        "(https://www.logan.qld.gov.au/MyLogan), for example "
        "'12 Ashton Street Kingston'."
    )
}

PARAM_TRANSLATIONS = {
    "en": {
        "property_location": "Street Address",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "property_location": (
            "Your street address, e.g. '12 Ashton Street Kingston'. "
            "The closest match from the MyLogan address search is used."
        ),
    },
}

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "referer": URL + "/MyLogan",
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
    "green waste": Icons.ORGANIC,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.logan.qld.gov.au",
    argument_name="property_location",
    max_results=1,
    headers=HEADERS,
    use_curl_cffi=True,
    date_format="%A %d %B %Y",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, property_location: str):
        self._property_location = " ".join(property_location.split())
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._property_location)
