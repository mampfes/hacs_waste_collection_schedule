from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Ballina Shire Council"
DESCRIPTION = "Source for Ballina Shire Council, NSW, Australia."
URL = "https://www.ballina.nsw.gov.au/Residents/Waste-and-Recycling/Bin-Collection-Day"
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the full service address used by Ballina Shire Council, for example "
        "'1 Grant St, Ballina NSW 2478'."
    )
}
TEST_CASES = {
    "1/49 Grant Street BALLINA": {"address": "1/49 Grant Street BALLINA"},
    "2/7 Hartigan St CUMBALUM": {"address": "2/7 Hartigan St CUMBALUM"},
}

PAGE_LINK = "/$8a878053-5e29-431d-896b-8c79ce08799f$/Residents/Waste-and-Recycling/Bin-Collection-Day"

# Ballina sits behind Akamai, which fingerprints the TLS handshake as well as
# the headers. Announcing Chrome in the User-Agent over a plain `requests`
# handshake is the worst of both worlds and is served a 403 "Access Denied"
# page; curl_cffi's Chrome impersonation makes the two agree and passes.
HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "referer": URL,
    "x-requested-with": "XMLHttpRequest",
}

ICON_MAP = {
    "general waste": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
    "green organics": Icons.ORGANIC,
    "food organics": Icons.BIO_KITCHEN,
    "garden organics": Icons.GARDEN,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.ballina.nsw.gov.au",
    search_fuzzy=True,
    # Ballina's fuzzy search ranks poorly: "1 Grant St, Ballina NSW 2478"
    # comes back with "2/7 Hartigan St CUMBALUM" first and the Grant Street
    # properties behind it. Capping at one result therefore guaranteed the
    # wrong property, so take the whole list and disambiguate it here.
    page_link=PAGE_LINK,
    headers=HEADERS,
    use_curl_cffi=True,
    search_response_format="json_then_xml",
    strict_address_matching=True,
    strict_single_result=True,
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, address: str):
        self._address = " ".join(address.split())
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._address)
