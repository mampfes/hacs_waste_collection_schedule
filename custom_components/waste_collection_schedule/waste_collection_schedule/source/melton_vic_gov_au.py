from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Melton City Council"
DESCRIPTION = "Source for Melton City Council rubbish collection."
URL = "https://www.melton.vic.gov.au"
TEST_CASES = {
    "Melton": {"street_address": "1 HIGH STREET MELTON 3337"},
    "Melton South": {"street_address": "3 BRIDGE ROAD MELTON SOUTH 3338"},
    "Fraser Rise": {"street_address": "20 ASPIRE BOULEVARD FRASER RISE 3336"},
    "Cobblebank": {"street_address": "2-26 FERRIS ROAD COBBLEBANK 3338"},
}

ICON_MAP = {
    "Food and Green Waste": Icons.BIO_KITCHEN,
    "Hard Waste": Icons.BULKY,
    "Recycling": Icons.RECYCLING,
}

# Melton sits behind Akamai, which scores the TLS/HTTP fingerprint as well as
# the headers: plain `requests` is served a 403 "Access Denied" page for every
# request, including the warm-up. curl_cffi's Chrome impersonation passes.
# The Accept header is what keeps the search endpoint answering JSON -- without
# it, content negotiation hands back the legacy XML shape instead.
HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "x-requested-with": "XMLHttpRequest",
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.melton.vic.gov.au",
    argument_name="street_address",
    headers=HEADERS,
    use_curl_cffi=True,
    search_response_format="json_then_xml",
    warm_up_url="https://www.melton.vic.gov.au/My-Area",
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._street_address)
