from datetime import datetime

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.WhitespaceWRP import WhitespaceClient

TITLE = "Waverley Borough Council"
DESCRIPTION = "Source for www.waverley.gov.uk services for Waverley Borough Council."
URL = "https://waverley.gov.uk"
TEST_CASES = {
    "Example": {
        "address_postcode": "GU8 5QQ",
        "address_name_numer": "1",
        "address_street": "Gasden Drive",
    },
    "Example No Postcode Space": {
        "address_postcode": "GU85QQ",
        "address_name_numer": "1",
        "address_street": "Gasden Drive",
    },
}
ICON_MAP = {
    "Domestic Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
    "Food Waste": "mdi:food-apple",
}

API_URL = "https://wav-wrp.whitespacews.com/"


class Source:
    def __init__(
        self,
        address_name_numer=None,
        address_street=None,
        street_town=None,
        address_postcode=None,
    ):
        self._address_name_numer = address_name_numer
        self._address_street = address_street
        self._street_town = street_town
        self._address_postcode = address_postcode
        self._client = WhitespaceClient(API_URL)

    def fetch(self):
        schedule = self._client.fetch_schedule(
            address_name_number=self._address_name_numer,
            address_postcode=self._address_postcode,
            address_street=self._address_street,
            street_town=self._street_town,
        )

        entries = []
        for date_str, type_str in schedule:
            collection_type = type_str.replace(" Collection Service", "")
            entries.append(
                Collection(
                    date=datetime.strptime(date_str, "%d/%m/%Y").date(),
                    t=type_str,
                    icon=ICON_MAP.get(collection_type),
                )
            )
        return entries
