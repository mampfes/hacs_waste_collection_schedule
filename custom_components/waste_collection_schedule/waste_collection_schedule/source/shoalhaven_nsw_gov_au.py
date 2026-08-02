from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Shoalhaven City Council"
DESCRIPTION = "Source script for shoalhaven.nsw.gov.au"
URL = "https://www.shoalhaven.nsw.gov.au/"
TEST_CASES = {
    # Example Geolocation ID from the provided URL.
    "Elizabeth Dr, VINCENTIA": {
        "geolocation_id": "2ea7b0c7-b627-421d-8436-248b8da384b6"
    },
    "The Park Dr, SANCTUARY POINT": {
        "geolocation_id": "b0b35bab-76c1-4b58-b609-115da3fa3829"
    },
    "Station St, NOWRA": {"geolocation_id": "984061de-cd63-43f4-bbd3-694b4e8af4d5"},
}

ICON_MAP = {
    "general waste": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
}

# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": """
    To get your Geolocation ID:
    1. Go to the Shoalhaven City Council 'My Area' page: <https://www.shoalhaven.nsw.gov.au/My-Area>
    2. Open Developer Tools in your browser by pressing F12 and go to the Network tab.
    3. Enter your address in the search bar and select it from the suggestions.
    4. Once your address information is displayed, look at the 'wasteservices' URL in the Network tab.
    5. Copy the long string of letters and numbers that follows 'geolocationid=' (e.g., 2ea7b0c7-b627-421d-8436-248b8da384b6). This is your Geolocation ID.
    """,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "geolocation_id": "Your unique Geolocation ID for the address (e.g., 2ea7b0c7-b627-421d-8436-248b8da384b6)",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "geolocation_id": "Geolocation ID",
    },
}

# ### End of arguments affecting the configuration GUI ####

_CONFIG = OpenCitiesConfig(
    domain="https://www.shoalhaven.nsw.gov.au",
    argument_name="geolocation_id",
    icon_keywords=ICON_MAP,
    require_date_precise=True,
)


class Source:
    def __init__(self, geolocation_id: str):
        """
        Initialize the Source with the provided geolocation ID.

        :param geolocation_id: The unique ID for the address to fetch waste services for.
        """
        self._geolocation_id = geolocation_id
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(geolocation_id=self._geolocation_id)
