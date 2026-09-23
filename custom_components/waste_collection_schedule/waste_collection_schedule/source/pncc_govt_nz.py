from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Palmerston North City Council"
DESCRIPTION = (
    "Source for Palmerston North City Council rubbish and recycling collections."
)
URL = "https://www.pncc.govt.nz/Services/Rubbish-and-recycling/Palmy-Collections/Rubbish-and-recycling-days"
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your street address as it appears in the search on the Palmerston "
        "North City Council 'Rubbish and recycling days' page, for example "
        "'8 Swansea Street Palmerston North'."
    )
}
TEST_CASES = {
    "8 Swansea Street, Hokowhitu": {"address": "8 Swansea Street Palmerston North"},
    "1 Broadway Avenue": {"address": "1 Broadway Avenue Palmerston North"},
}

ICON_MAP = {
    "rubbish": Icons.GENERAL_WASTE,
    "wheelie bin": Icons.RECYCLING,
    "recycling": Icons.RECYCLING,
    "glass": Icons.GLASS,
}

_CONFIG = OpenCitiesConfig(
    domain="https://www.pncc.govt.nz",
    headers={"Accept": "application/json"},
    use_curl_cffi=True,
    icon_keywords=ICON_MAP,
)


class Source:
    def __init__(self, address: str):
        self._address = " ".join(address.split())
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        return self._client.fetch(address=self._address)
