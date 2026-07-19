from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Unley City Council (SA)"
DESCRIPTION = "Source for Unley City Council rubbish collection."
URL = "https://www.unley.sa.gov.au/"
TEST_CASES = {
    "Test1": {
        "post_code": "5061",
        "suburb": "Malvern",
        "street_name": "Wattle Street",
        "street_number": "188",
    },
    "Test2": {
        "post_code": 5061,
        "suburb": "Unley",
        "street_name": "Unley Road",
        "street_number": "192",
    },
    "Test3": {
        "post_code": "5063",
        "suburb": "Parkside",
        "street_name": "Castle Street",
        "street_number": 63,
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

ICON_MAP = {
    "General Waste (Blue Bin)": Icons.GENERAL_WASTE,
    "Organic Waste (Green or Grey Bin)": Icons.ORGANIC,
    "Recycling (Yellow Lid Bin)": Icons.RECYCLING,
    "Residential Street Cleaning": Icons.GENERAL_WASTE,
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Green Waste": Icons.GARDEN,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.unley.sa.gov.au",
    argument_name="street_name",
    search_response_format="xml",
    headers=HEADERS,
    use_curl_cffi=True,
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(
        self, post_code: str, suburb: str, street_name: str, street_number: str | int
    ):
        self.post_code = post_code
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        address = (
            f"{self.street_number} {self.street_name} {self.suburb} SA {self.post_code}"
        )
        return self._client.fetch(address=address)
