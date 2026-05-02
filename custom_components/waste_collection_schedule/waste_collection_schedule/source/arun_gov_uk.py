from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentRequired
from waste_collection_schedule.service.uk_cloud9_apps import Cloud9Client

TITLE = "Arun District Council"
DESCRIPTION = "Source for arun.gov.uk services for Arun District, UK."
URL = "https://www.arun.gov.uk"
TEST_CASES = {
    "Test_001": {"postcode": "BN17 5JA", "address": "21A Beach Road, Littlehampton"},
    "Test_002": {"postcode": "BN16 1AA", "address": "2 Downs Way, East Preston"},
    "Test_003": {"uprn": 100062180214},
    "Test_004": {"uprn": "0100062180214"},
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You can find your UPRN by visiting [Find My Address](https://www.findmyaddress.co.uk) and entering your address details."
}
PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
        "postcode": "Postcode (legacy, use UPRN instead)",
        "address": "Address (legacy, use UPRN instead)",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
        "postcode": "Postcode (legacy, use UPRN instead)",
        "address": "Address (legacy, use UPRN instead)",
    }
}
ICON_MAP = {
    "garden": "mdi:leaf",
    "food": "mdi:food-apple",
    "recycl": "mdi:recycle",
    "waste": "mdi:trash-can",
    "rubbish": "mdi:trash-can",
    "refuse": "mdi:trash-can",
}


class Source:
    def __init__(
        self,
        uprn: str | int | None = None,
        postcode: str | None = None,
        address: str | None = None,
    ):
        self._client = Cloud9Client("arun", icon_keywords=ICON_MAP)
        self._uprn = str(uprn) if uprn else None
        self._postcode = postcode
        self._address = address

    def fetch(self) -> list[Collection]:
        if self._uprn:
            return self._client.fetch_by_uprn(self._uprn)
        if not self._postcode:
            raise SourceArgumentRequired("uprn", "Provide a UPRN or postcode + address")
        return self._client.fetch_by_address(
            postcode=self._postcode,
            address_string=self._address or "",
            argument_name="postcode",
        )
