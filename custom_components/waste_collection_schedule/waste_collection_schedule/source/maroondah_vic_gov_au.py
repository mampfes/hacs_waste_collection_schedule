from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Maroondah City Council"
DESCRIPTION = "Source for Maroondah City Council. Finds both green waste and general recycling dates."
URL = "https://www.maroondah.vic.gov.au"
TEST_CASES = {
    "Monday - Area A": {"address": "1 Abbey Court, RINGWOOD 3134"},  # Monday - Area A
    "Monday - Area B": {
        "address": "1 Angelica Crescent, CROYDON HILLS 3136"
    },  # Monday - Area B
    "Tuesday - Area B": {"address": "6 Como Close, CROYDON 3136"},  # Tuesday - Area B
    "Wednesday - Area A": {
        "address": "113 Dublin Road, RINGWOOD EAST 3135"
    },  # Wednesday - Area A
    "Wednesday - Area B": {
        "address": "282 Maroondah Highway, RINGWOOD 3134"
    },  # Wednesday - Area B
    "Thursday - Area A": {
        "address": "4 Albury Court, CROYDON NORTH 3136"
    },  # Thursday - Area A
    "Thursday - Area B": {
        "address": "54 Lincoln Road, CROYDON 3136"
    },  # Thursday - Area B
    "Friday - Area A": {
        "address": "6 Lionel Crescent, CROYDON 3136"
    },  # Friday - Area A
    "Friday - Area B": {"address": "61 Timms Avenue, KILSYTH 3137"},  # Friday - Area B
}

ICON_MAP = {
    "General waste": Icons.GENERAL_WASTE,
    "Food and Garden organics": Icons.BIO_KITCHEN,
    "Hard Waste": Icons.BULKY,
    "Recycling": Icons.RECYCLING,
}

# The council website sits behind Akamai bot protection, which rejects
# python's TLS fingerprint with 403. Impersonating a browser via curl_cffi
# and sending XHR-style headers gets through (same approach as
# blacktown_nsw_gov_au and ryde_nsw_gov_au).
HEADERS = {
    "Accept": "text/plain, */*; q=0.01",
    "Referer": "https://www.maroondah.vic.gov.au/Residents-property/Waste-rubbish/Waste-collection-schedule",
    "X-Requested-With": "XMLHttpRequest",
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.maroondah.vic.gov.au",
    use_curl_cffi=True,
    headers=HEADERS,
    warm_up_url="https://www.maroondah.vic.gov.au/Residents-property/Waste-rubbish/Waste-collection-schedule",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, address: str):
        self._street_address = address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
