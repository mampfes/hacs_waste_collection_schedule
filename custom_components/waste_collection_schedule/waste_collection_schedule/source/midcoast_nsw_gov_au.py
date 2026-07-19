from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "MidCoast Council"
DESCRIPTION = "Source for MidCoast Council (NSW) rubbish collection."
URL = "https://www.midcoast.nsw.gov.au/"
DEEPLINK = f"{URL}Services/Waste-and-recycling/When-is-my-bin-collected"
TEST_CASES = {
    "Randomly Selected Address": {"street_address": "101 Goldens Road, FORSTER"}
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Green Waste": Icons.GARDEN,
}

_CONFIG = OpenCitiesConfig(
    domain=URL.rstrip("/"),
    argument_name="street_address",
    warm_up_url=URL,
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        entries = self._client.fetch(address=self._street_address)
        # The wasteservices response for MidCoast also includes non-waste
        # articles (e.g. bin-collection guidelines); only keep the known
        # waste types, matching the pre-migration allowlist behaviour.
        return [entry for entry in entries if entry.type in ICON_MAP]
