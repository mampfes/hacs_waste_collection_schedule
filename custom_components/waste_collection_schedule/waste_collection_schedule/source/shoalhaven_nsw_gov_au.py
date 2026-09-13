from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentExceptionMultiple
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Shoalhaven City Council"
DESCRIPTION = "Source script for shoalhaven.nsw.gov.au"
URL = "https://www.shoalhaven.nsw.gov.au/"
TEST_CASES = {
    "2 Cherry Plum Way, WORRIGEE": {"street_address": "2 Cherry Plum Way, WORRIGEE"},
    "10 Station Street, NOWRA": {"street_address": "10 Station Street, NOWRA"},
    "3 The Park Drive, SANCTUARY POINT": {
        "street_address": "3 The Park Drive, SANCTUARY POINT"
    },
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
    Enter your street address as the council's own address search shows it,
    e.g. "2 Cherry Plum Way, WORRIGEE". You can check it on the
    <https://www.shoalhaven.nsw.gov.au/My-Area> page.

    A Geolocation ID may be given instead of an address, and takes precedence
    when both are set. To find it:
    1. Go to the Shoalhaven City Council 'My Area' page: <https://www.shoalhaven.nsw.gov.au/My-Area>
    2. Open Developer Tools in your browser by pressing F12 and go to the Network tab.
    3. Enter your address in the search bar and select it from the suggestions.
    4. Once your address information is displayed, look at the 'wasteservices' URL in the Network tab.
    5. Copy the long string of letters and numbers that follows 'geolocationid=' (e.g., 2ea7b0c7-b627-421d-8436-248b8da384b6). This is your Geolocation ID.
    """,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": "Your street address, e.g. 2 Cherry Plum Way, WORRIGEE",
        "geolocation_id": "Your unique Geolocation ID for the address (e.g., 2ea7b0c7-b627-421d-8436-248b8da384b6). Only needed if the address search cannot find your property.",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_address": "Street address",
        "geolocation_id": "Geolocation ID",
    },
}

# ### End of arguments affecting the configuration GUI ####

_CONFIG = OpenCitiesConfig(
    domain="https://www.shoalhaven.nsw.gov.au",
    # The address-only path is the one users take, so name that argument in
    # the exceptions the client raises -- except when the visitor supplied the
    # geolocation id instead, which is the argument to flag then.
    argument_name="street_address",
    direct_argument_name="geolocation_id",
    icon_keywords=ICON_MAP,
    require_date_precise=True,
    # The council sits behind Akamai, which fingerprints the TLS handshake as
    # well as the headers: the address search answers 403 to plain
    # requests/urllib3 no matter what User-Agent it announces. curl_cffi's
    # Chrome impersonation makes the handshake match the claim and passes.
    use_curl_cffi=True,
    # Without an explicit Accept header the search endpoint returns XML
    # instead of JSON.
    headers={"Accept": "application/json"},
)


class Source:
    def __init__(
        self,
        street_address: str | None = None,
        geolocation_id: str | None = None,
    ):
        """
        Initialize the Source with a street address or a geolocation ID.

        :param street_address: The address to look up, as the council's address
            search shows it, e.g. "2 Cherry Plum Way, WORRIGEE".
        :param geolocation_id: The unique ID for the address to fetch waste
            services for, used in preference to ``street_address`` when given.
        """
        if street_address is None and geolocation_id is None:
            raise SourceArgumentExceptionMultiple(
                ["street_address", "geolocation_id"],
                "Either street_address or geolocation_id must have a value",
            )

        self._street_address = street_address
        self._geolocation_id = geolocation_id
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(
            address=self._street_address, geolocation_id=self._geolocation_id
        )
