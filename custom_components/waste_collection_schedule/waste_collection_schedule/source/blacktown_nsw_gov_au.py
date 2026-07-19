from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Blacktown City Council (NSW)"
DESCRIPTION = "Source for Blacktown City Council rubbish collection."
URL = "https://www.blacktown.nsw.gov.au/"
TEST_CASES = {
    "Plumpton Marketplace": {
        "post_code": "2761",
        "suburb": "Plumpton",
        "street_name": "Jersey Rd",
        "street_number": "260",
    },
    "Rooty Hill Tennis & Squash Centre": {
        "post_code": "2766",
        "suburb": "Rooty Hill",
        "street_name": "Learmonth St",
        "street_number": "13-15",
    },
    "Workers Blacktown": {
        "post_code": "2148",
        "suburb": "Blacktown",
        "street_name": "Campbell Street",
        "street_number": "18",
    },
    "Hythe St": {
        "post_code": "2770",
        "suburb": "Mount Druitt",
        "street_name": "Hythe St",
        "street_number": "9-11",
    },
    "Issue#4434": {
        "post_code": "2762",
        "suburb": "Tallawong",
        "street_name": "Coffey St",
        "street_number": "13",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/plain, */*; q=0.01",
    "Referer": "https://www.blacktown.nsw.gov.au/Services/Waste-services-and-collection/Bin-collection-and-new-service-delivery-days",
    "X-Requested-With": "XMLHttpRequest",
}


ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.blacktown.nsw.gov.au",
    argument_name="street_name",
    headers=HEADERS,
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
        address = f"{self.street_number} {self.street_name}, {self.suburb} NSW {self.post_code}"
        return self._client.fetch(address=address)
