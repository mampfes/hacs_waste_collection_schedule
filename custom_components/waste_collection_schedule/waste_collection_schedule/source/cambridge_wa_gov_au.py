from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentExceptionMultiple
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Town of Cambridge (WA)"
DESCRIPTION = "Source for Town of Cambridge (Western Australia) rubbish collection."
URL = "https://www.cambridge.wa.gov.au"
TEST_CASES = {
    "Geolocation ID": {"geolocation_id": "ec16b372-7aab-4082-8519-2163c431777d"},
    "Cambridge Library": {"street_address": "99 The Boulevard, FLOREAT 6014"},
}

ICON_MAP = {
    "general waste": Icons.GENERAL_WASTE,
    "green waste": Icons.GARDEN,
    "fogo": Icons.ORGANIC,
    "recycling": Icons.RECYCLING,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.cambridge.wa.gov.au",
    use_curl_cffi=True,
    warm_up_url="https://www.cambridge.wa.gov.au/Residents/Waste-Recycling/Find-My-Bin-Day",
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
