from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentRequired
from waste_collection_schedule.service.uk_cloud9_apps import Cloud9Client

TITLE = "East Devon District Council"
DESCRIPTION = "Source for East Devon services for East Devon District Council, UK."
URL = "https://eastdevon.gov.uk/"
COUNTRY = "uk"
TEST_CASES = {
    "Test_001": {"uprn": "010000246114"},
    "Test_002": {"uprn": 10000272679},
    "Test_003": {"postcode": "EX8 2AN", "address": "1 Dagmar Road"},
    "Test_004": {"postcode": "EX5 2AB", "address": "1 Blackhorse Cottages"},
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Either give your UPRN, or give your postcode together with your address. You can find your UPRN by visiting [Find My Address](https://www.findmyaddress.co.uk) and entering your address details, or from the UPRN query parameter on the East Devon bin collection page."
}
PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
        "postcode": "Postcode",
        "address": "Address",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
        "postcode": "Postcode, e.g. EX8 2AN. Use together with address instead of a UPRN.",
        "address": "House name or number and street, e.g. 1 Dagmar Road. Use together with postcode instead of a UPRN.",
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
    def __init__(
        self,
        uprn: str | int | None = None,
        postcode: str | None = None,
        address: str | None = None,
    ):
        self._client = Cloud9Client("eastdevon", icon_keywords=ICON_MAP)
        # Existing configurations pass a bare UPRN, which this API wants
        # zero-padded to 12 digits. Keep the padding so they keep working.
        self._uprn = str(uprn).zfill(12) if uprn else None
        self._postcode = postcode
        self._address = address

    def fetch(self) -> list[Collection]:
        if self._uprn:
            return self._client.fetch_by_uprn(self._uprn)
        if not self._postcode:
            raise SourceArgumentRequired(
                "uprn", "Provide a UPRN, or a postcode together with an address"
            )
        return self._client.fetch_by_address(
            postcode=self._postcode,
            address_string=self._address or "",
            argument_name="postcode",
        )
