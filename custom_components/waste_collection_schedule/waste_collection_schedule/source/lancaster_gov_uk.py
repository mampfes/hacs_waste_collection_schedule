import logging
from datetime import datetime
from typing import Union

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.WhitespaceWRP import WhitespaceClient

TITLE = "Lancaster City Council"
DESCRIPTION = "Source for lancaster.gov.uk services for Lancaster City Council, UK."
URL = "https://lancaster.gov.uk"
TEST_CASES = {
    "1 Queen Street Lancaster, LA1 1RS": {"house_number": 1, "postcode": "LA1 1RS"}
}
API_URL = "https://lcc-wrp.whitespacews.com"
ICON_MAP = {
    "Domestic Waste": "mdi:trash-can",
    "Garden Waste": "mdi:leaf",
    # Dynamic (non-PDF) calendar does not split the types of recycling other than garden and food.
    "Recycling": "mdi:recycle",
    "Food Waste": "mdi:food",
}
SUFFIXES = (
    " Collection Service",
    " Collection - refer to calendar for stream",
)

_LOGGER = logging.getLogger(__name__)


def _clean_collection_type(type_text: str) -> str:
    for suffix in SUFFIXES:
        if type_text.endswith(suffix):
            return type_text[: -len(suffix)].strip()
    return type_text.strip()


class Source:
    def __init__(
        self, postcode: str, house_number: Union[int, str, None] = None
    ) -> None:
        self._house_number = house_number
        self._postcode = postcode
        self._client = WhitespaceClient(API_URL)

    def fetch(self):
        schedule = self._client.fetch_schedule(
            address_name_number=self._house_number,
            address_postcode=self._postcode,
            address_street="",
        )

        entries = []
        for date_str, type_str in schedule:
            collection_type = next(
                (key for key in ICON_MAP if type_str.startswith(key)),
                _clean_collection_type(type_str),
            )
            try:
                entries.append(
                    Collection(
                        date=datetime.strptime(date_str, "%d/%m/%Y").date(),
                        t=collection_type,
                        icon=ICON_MAP.get(collection_type, "mdi:trash-can"),
                    )
                )
            except ValueError:
                _LOGGER.info(f"Skipped {date_str} as it does not match date format")
        return entries
