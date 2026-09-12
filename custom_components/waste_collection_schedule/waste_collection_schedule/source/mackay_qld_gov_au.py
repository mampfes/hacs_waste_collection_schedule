from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Mackay Regional Council"
DESCRIPTION = "Source for Mackay Regional Council rubbish collection."
URL = "https://www.mackay.qld.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "Mackay (Monday)": {"address": "77 Wood Street Mackay"},
    "West Mackay (Thursday)": {"address": "115 Nebo Road West Mackay"},
    "Sarina Beach (Wednesday)": {"address": "891 Sarina Beach Road Sarina Beach"},
    "Alligator Creek (Tuesday)": {"address": "184 Hay Point Road Alligator Creek"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your street address as used on the council's rubbish and bins page "
        "(https://www.mackay.qld.gov.au/residents/services/waste), for example "
        "'77 Wood Street Mackay'."
    )
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": (
            "Your street address, e.g. '77 Wood Street Mackay'. The closest match "
            "from the council's address search is used."
        ),
    },
}

# Mackay sits behind Akamai, which scores the TLS/HTTP fingerprint as well as
# the headers: plain `requests` carrying a browser User-Agent is served a 403
# "Access Denied" page. curl_cffi's Chrome impersonation passes.
HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "referer": URL + "/residents/services/waste",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
}

ICON_MAP = {
    "general waste": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
    "green waste": Icons.ORGANIC,
}

_CONFIG = OpenCitiesConfig(
    domain=URL,
    argument_name="address",
    max_results=1,
    headers=HEADERS,
    use_curl_cffi=True,
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, address: str):
        self._address = " ".join(address.split())
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._address)
