from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentExceptionMultiple
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Banyule City Council"
DESCRIPTION = "Source for Banyule City Council rubbish collection."
URL = "https://www.banyule.vic.gov.au"
TEST_CASES = {
    "Monday A": {"street_address": "6 Mandall Avenue, IVANHOE"},
    "Monday A Geolocation ID": {
        "geolocation_id": "486d9d83-8377-4709-987f-4627beaa0ac8"
    },
    "Monday B": {"street_address": "10 Burke Road North, IVANHOE EAST"},
    "Thursday A": {"street_address": "255 St Helena Road, GREENSBOROUGH"},
    "Thursday B": {"street_address": "35 Para Road, MONTMORENCY"},
}

ICON_MAP = {
    "green waste": Icons.GARDEN,
    "recycling": Icons.RECYCLING,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.banyule.vic.gov.au",
    use_curl_cffi=True,
    impersonate="chrome124",
    warm_up_url="https://www.banyule.vic.gov.au/Waste-environment/Waste-recycling/Bin-collection-services",
    warm_up_before="wasteservices",
    icon_keywords=ICON_MAP,
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
