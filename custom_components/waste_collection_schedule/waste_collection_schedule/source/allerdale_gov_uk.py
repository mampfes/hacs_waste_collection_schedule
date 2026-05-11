from datetime import datetime

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.WhitespaceWRP import WhitespaceClient

TITLE = "Allerdale Borough Council"
DESCRIPTION = "Source for www.allerdale.gov.uk services for Allerdale Borough Council."
URL = "https://www.allerdale.gov.uk"
TEST_CASES = {
    "Keswick": {
        "address_postcode": "CA12 4HU",
        "address_name_number": "11",
    },
    "Workington": {
        "address_postcode": "CA14 3NS",
        "address_name_number": "177",
    },
    "Wigton": {
        "address_postcode": "CA7 9RS",
        "address_name_number": "55",
    },
}
ICON_MAP = {
    "Domestic Waste": "mdi:trash-can",
    "Glass Cans and Plastic Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}
API_URL = "https://abc-wrp.whitespacews.com/"


class Source:
    def __init__(
        self,
        address_name_number=None,
        address_postcode=None,
    ):
        self._address_name_number = address_name_number
        self._address_postcode = address_postcode
        self._client = WhitespaceClient(API_URL)

    def fetch(self):
        schedule = self._client.fetch_schedule(
            address_name_number=self._address_name_number,
            address_postcode=self._address_postcode,
        )

        entries = []
        for date_str, type_str in schedule:
            collection_type = type_str.replace(" Collection", "").replace(" Service", "")
            entries.append(
                Collection(
                    date=datetime.strptime(date_str, "%d/%m/%Y").date(),
                    t=type_str,
                    icon=ICON_MAP.get(collection_type),
                )
            )
        return entries
