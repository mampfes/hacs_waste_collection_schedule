from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Moorabool Shire Council"
DESCRIPTION = "Source for Moorabool Shire Council rubbish collection."
URL = "https://www.moorabool.vic.gov.au"


HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Go to <https://www.moorabool.vic.gov.au/Waste-and-environment/Household-bins/Find-your-bin-collection-day> and make sure your address matches the auto-complete suggestions."
}

TEST_CASES = {
    "Border Inn Hotel": {
        "address": "139 Main Street Bacchus Marsh 3340",
    },
    "Bendigo Bank": {
        "address": "191 Main Street Bacchus Marsh 3340",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/plain, */*; q=0.01",
    "Referer": "https://www.moorabool.vic.gov.au/Waste-and-environment/Household-bins/Find-your-bin-collection-day",
    "X-Requested-With": "XMLHttpRequest",
}


ICON_MAP = {
    "Garbage": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Green waste": Icons.GARDEN,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.moorabool.vic.gov.au",
    headers=HEADERS,
    use_curl_cffi=True,
    icon_keywords=ICON_MAP,
    strip_type_suffixes=("collection",),
)


class Source:
    def __init__(self, address: str):
        self.address = address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self.address)
