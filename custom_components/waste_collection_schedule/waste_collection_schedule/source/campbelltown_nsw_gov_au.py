from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Campbelltown City Council (NSW)"
DESCRIPTION = "Source for Campbelltown City Council rubbish collection."
URL = "https://www.campbelltown.nsw.gov.au/"
TEST_CASES = {
    "Minto Mall": {
        "post_code": "2566",
        "suburb": "Minto",
        "street_name": "Brookfield Road",
        "street_number": "10",
    },
    "Campbelltown Catholic Club": {
        "post_code": "2560",
        "suburb": "Campbelltown",
        "street_name": "Camden Road",
        "street_number": "20-22",
    },
    "Australia Post Ingleburn": {
        "post_code": "2565",
        "suburb": "INGLEBURN",
        "street_name": "Oxford Road",
        "street_number": "34",
    },
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Green Waste": Icons.GARDEN,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.campbelltown.nsw.gov.au",
    argument_name="street_name",
    search_response_format="json_then_xml",
    use_curl_cffi=True,
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(
        self, post_code: str, suburb: str, street_name: str, street_number: str
    ):
        self.post_code = post_code
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        address = f"{self.street_number} {self.street_name} {self.suburb} NSW {self.post_code}"
        return self._client.fetch(address=address)
