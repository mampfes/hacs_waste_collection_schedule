from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "City of Ryde (NSW)"
DESCRIPTION = "Source for City of Ryde rubbish collection."
URL = "https://www.ryde.nsw.gov.au/"
TEST_CASES = {
    "Ryde Aquatic Centre": {
        "post_code": "2112",
        "suburb": "Ryde",
        "street_name": "Victoria Road",
        "street_number": "504",
    },
    "Harris Farm Markets Boronia Park": {
        "post_code": "2111",
        "suburb": "Gladesville",
        "street_name": "Pittwater Road",
        "street_number": "128",
    },
    "Eastwood Shopping Centre": {
        "post_code": "2122",
        "suburb": "Eastwood",
        "street_name": "Rowe Street",
        "street_number": "152",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/plain, */*; q=0.01",
    "Referer": "https://www.ryde.nsw.gov.au/Environment-and-Waste/Waste-and-Recycling",
    "X-Requested-With": "XMLHttpRequest",
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Green Waste": Icons.GARDEN,
    "Garden Organics": Icons.GARDEN,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.ryde.nsw.gov.au",
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
        address = (
            f"{self.street_number} {self.street_name} {self.suburb} {self.post_code}"
        )
        return self._client.fetch(address=address)
