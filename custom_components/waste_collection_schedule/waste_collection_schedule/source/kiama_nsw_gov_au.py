from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Kiama City Council"
DESCRIPTION = "Source script for kiama.nsw.gov.au"
URL = "https://kiama.nsw.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "TestName1": {"geolocationid": "38da9173-322a-43fd-953b-3b51803dbe94"},
    "TestName2": {"geolocationid": "f2c04fcf-e3d3-424e-aa90-1d365bbf0130"},
}

ICON_MAP = {
    "Urban garbage": Icons.GENERAL_WASTE,
    "Urban food & garden organics": Icons.BIO_KITCHEN,
    "Urban recycling": Icons.RECYCLING,
}


HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": """Go to <https://www.kiama.nsw.gov.au/Services/Waste-and-recycling/Find-my-bin-collection-dates>
Open the developer tools (F12), Go to the Network tab
Put in your address, and click Search.

Look for a network call to the wasteservices endpoint, it will have geolocationid=<GUID>
This GUID is what you need, it is unique to your service address.""",
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.kiama.nsw.gov.au",
    argument_name="geolocationid",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, geolocationid: str):
        self._geolocationid = geolocationid
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(geolocation_id=self._geolocationid)
