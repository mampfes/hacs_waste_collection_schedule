from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.uk_cloud9_apps import Cloud9Client

TITLE = "Rugby Borough Council"
DESCRIPTION = "Source for Rugby Borough Council, UK."
URL = "https://www.rugby.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": 100070200377},
    "Test_002": {"uprn": "100070200372"},
    "Test_003": {"uprn": "010010521297"},
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You can find your UPRN by visiting [Find My Address](https://www.findmyaddress.co.uk) and entering your address details."
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
    "recycl": "mdi:recycle",
    "rubbish": "mdi:trash-can",
    "garden": "mdi:leaf",
    "refuse": "mdi:trash-can",
}


class Source:
    def __init__(self, uprn: str | int):
        self._client = Cloud9Client("rugby", icon_keywords=ICON_MAP)
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        return self._client.fetch_by_uprn(self._uprn)
