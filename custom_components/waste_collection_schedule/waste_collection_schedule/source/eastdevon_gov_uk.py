from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.uk_cloud9_apps import Cloud9Client

TITLE = "East Devon District Council"
DESCRIPTION = "Source for East Devon services for East Devon District Council, UK."
URL = "https://eastdevon.gov.uk/"
COUNTRY = "uk"
TEST_CASES = {
    "Test_001": {"uprn": "010000246114"},
    "Test_002": {"uprn": 10000272679},
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You can find your UPRN by visiting [Find My Address](https://www.findmyaddress.co.uk) and entering your address details, or from the UPRN query parameter on the East Devon bin collection page."
}
PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}
ICON_MAP = {
    "refuse": Icons.GENERAL_WASTE,
    "rubbish": Icons.GENERAL_WASTE,
    "recycl": Icons.RECYCLING,
    "food": Icons.BIO_KITCHEN,
    "green": Icons.GARDEN,
    "garden": Icons.GARDEN,
}
SOURCE_CODEOWNERS = ["@SimonRice"]


class Source:
    def __init__(self, uprn: str | int):
        self._client = Cloud9Client("eastdevon", icon_keywords=ICON_MAP)
        self._uprn = str(uprn).zfill(12)

    def fetch(self) -> list[Collection]:
        return self._client.fetch_by_uprn(self._uprn)
