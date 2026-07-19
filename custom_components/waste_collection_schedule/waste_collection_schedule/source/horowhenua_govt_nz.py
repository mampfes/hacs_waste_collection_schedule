from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Horowhenua District Council"
DESCRIPTION = "Source for Horowhenua District Council Rubbish & Recycling collection."
URL = "https://www.horowhenua.govt.nz/"
TEST_CASES = {
    "House-Shannon": {
        "post_code": "4821",
        "town": "Shannon",
        "street_name": "Bryce Street",
        "street_number": "55",
    },
    "House-Levin": {
        "post_code": "5510",
        "town": "Levin",
        "street_name": "McKenzie Street",
        "street_number": "15",
    },
    "Commercial-Foxton": {
        "post_code": "4814",
        "town": "Foxton",
        "street_name": "State Highway 1",
        "street_number": "18",
    },
}

HEADERS = {
    "user-agent": "Mozilla/5.0",
    # Without an explicit Accept header the search endpoint returns XML
    # instead of JSON.
    "Accept": "application/json",
}

ICON_MAP = {
    "Rubbish": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.horowhenua.govt.nz",
    argument_name="street_name",
    headers=HEADERS,
    warm_up_url="https://www.horowhenua.govt.nz",
    use_curl_cffi=True,
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, post_code: str, town: str, street_name: str, street_number: str):
        self.post_code = post_code
        self.town = town.upper()
        self.street_name = street_name
        self.street_number = street_number
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        address = (
            f"{self.street_number} {self.street_name} {self.town} {self.post_code}"
        )
        return self._client.fetch(address=address)
