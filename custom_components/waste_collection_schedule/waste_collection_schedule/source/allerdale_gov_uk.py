from datetime import datetime

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.WhitespaceWRP import WhitespaceClient

TITLE = "Allerdale Borough Council"
DESCRIPTION = "Source for www.allerdale.gov.uk services for Allerdale Borough Council."
URL = "https://www.allerdale.gov.uk"
TEST_CASES = {
    "Keswick": {
        "postcode": "CA12 4HU",
        "house_number_or_name": "11",
    },
    "Workington": {
        "postcode": "CA14 3NS",
        "house_number_or_name": "177",
    },
    "Wigton": {
        "postcode": "CA7 9RS",
        "house_number_or_name": "55",
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
        house_number_or_name=None,
        postcode=None,
    ):
        self._address_name_number = house_number_or_name
        self._address_postcode = postcode
        self._client = WhitespaceClient(API_URL)

    def fetch(self):
        schedule = self._client.fetch_schedule(
            house_number_or_name=self._address_name_number,
            postcode=self._address_postcode,
        )

        entries = []
        for date_str, type_str in schedule:
            collection_type = type_str.replace(" Collection", "").replace(
                " Service", ""
            )
            entries.append(
                Collection(
                    date=datetime.strptime(date_str, "%d/%m/%Y").date(),
                    t=type_str,
                    icon=ICON_MAP.get(collection_type),
                )
            )
        return entries
