from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentRequired
from waste_collection_schedule.service.uk_cloud9_apps import Cloud9Client

TITLE = "Southend-on-Sea City Council"
DESCRIPTION = (
    "Source for southend.gov.uk services for Southend-on-Sea City Council, UK."
)
URL = "https://www.southend.gov.uk"
COUNTRY = "uk"
TEST_CASES = {
    "Test_001": {"uprn": 100090691871},
    "Test_002": {"uprn": "100090700485"},
    "Test_003": {
        "postcode": "SS3 9JD",
        "address": "38 Thorpedene Gardens, Shoeburyness",
    },
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
    "garden": Icons.GARDEN,
    "food": Icons.BIO_KITCHEN,
    "recycl": Icons.RECYCLING,
    "refuse": Icons.GENERAL_WASTE,
}


class Source:
    def __init__(
        self,
        uprn: str | int | None = None,
        postcode: str | None = None,
        address: str | None = None,
    ):
        self._client = Cloud9Client("southend", icon_keywords=ICON_MAP)
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
