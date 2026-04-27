from waste_collection_schedule import Collection
from waste_collection_schedule.service.uk_cloud9_apps import Cloud9Client

TITLE = "North Herts Council"
DESCRIPTION = "Source for www.north-herts.gov.uk services for North Herts Council."
URL = "https://www.north-herts.gov.uk/"
TEST_CASES = {
    "Example": {
        "postcode": "SG4 9QY",
        "address_name_numer": "26",
        "street": "BENSLOW RISE",
    },
    "Example No Postcode Space": {
        "postcode": "SG49QY",
        "address_name_numer": "26",
        "street": "BENSLOW RISE",
    },
    "Example fuzzy matching": {
        "postcode": "SG6 4EG",
        "address_name_numer": "4",
        "street": "Wilbury Road",
    },
    "Example garden waste": {
        "postcode": "SG8 5BN",
        "address_name_numer": "37",
        "street": "Heathfield",
    },
}
ICON_MAP = {
    "refuse": "mdi:trash-can",
    "residual": "mdi:trash-can",
    "recycle": "mdi:recycle",
    "recycling": "mdi:recycle",
    "garden": "mdi:leaf",
    "food": "mdi:food-apple",
    "paper": "mdi:package-variant",
    "card": "mdi:package-variant",
}


class Source:
    def __init__(
        self,
        address_name_numer: str | None = None,
        street: str | None = None,
        street_address: str | None = None,
        postcode: str | None = None,
    ):
        self._client = Cloud9Client("northherts", icon_keywords=ICON_MAP)
        self._address_name_numer = address_name_numer
        self._address_street = street
        self._street_town = street_address
        self._address_postcode = postcode

    def fetch(self) -> list[Collection]:
        search_query = " ".join(
            part.strip()
            for part in (
                self._address_name_numer,
                self._address_street,
                self._street_town,
                self._address_postcode,
            )
            if isinstance(part, str) and part.strip()
        )
        return self._client.fetch_by_address(
            postcode=self._address_postcode,
            address_string=search_query,
            address_name_number=self._address_name_numer,
            street=self._address_street,
            street_address=self._street_town,
            argument_name="postcode",
        )
