from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Mildura Rural City Council"
DESCRIPTION = "Source for Mildura Rural City Council waste collection."
URL = "https://www.mildura.vic.gov.au"
TEST_CASES = {
    "Stockmans Drive": {"street_address": "1 Stockmans Drive, Irymple VIC 3498"},
    "Deakin Avenue": {"street_address": "76 Deakin Avenue, Mildura VIC 3500"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": "Full street address including suburb and postcode, e.g. '1 Stockmans Drive, Irymple VIC 3498'",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Go to <https://www.mildura.vic.gov.au/Explore/My-Neighbourhood> and make sure your address matches the auto-complete suggestions."
}

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "accept": "text/plain, */*; q=0.01",
    "Referer": "https://www.mildura.vic.gov.au/Services/Waste-and-Recycling/My-bins/Find-your-bin-day",
    "X-Requested-With": "XMLHttpRequest",
}

ICON_MAP = {
    "Organics Waste": Icons.BIO_KITCHEN,
    "Landfill Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Glass": Icons.GLASS,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.mildura.vic.gov.au",
    argument_name="street_address",
    headers=HEADERS,
    use_curl_cffi=True,
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
