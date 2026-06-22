import logging
from typing import final

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.WhitespaceWRP import (
    WhitespaceParser,
    WhitespaceRetriever,
)
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
    preserved,
    resolve,
)

# Declarative source on the shared Whitespace WRP components (WhitespaceRetriever
# + WhitespaceParser). classify() maps the council's open-ended type labels onto
# canonical WasteTypes.

_LOGGER = logging.getLogger(__name__)

_TYPE_MAP = {
    "Domestic Waste": GENERAL_WASTE,
    "Glass Cans and Plastic Recycling": RECYCLABLES,
    "Garden Waste": GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Allerdale Borough Council"
    DESCRIPTION = (
        "Source for www.allerdale.gov.uk services for Allerdale Borough Council."
    )
    URL = "https://www.allerdale.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES = [GENERAL_WASTE, RECYCLABLES, GARDEN_WASTE]
    API_URL = "https://abc-wrp.whitespacews.com/"

    TEST_CASES = {
        "Keswick": {"address_postcode": "CA12 4HU", "address_name_number": "11"},
        "Workington": {"address_postcode": "CA14 3NS", "address_name_number": "177"},
        "Wigton": {"address_postcode": "CA7 9RS", "address_name_number": "55"},
    }

    PARAMS = [
        text_field("address_postcode", "Postcode"),
        text_field("address_name_number", "House name/number", optional=True),
    ]

    parse_date = date_parsers.for_format("%d/%m/%Y")

    retrieve = WhitespaceRetriever(
        name_number="address_name_number",
        postcode="address_postcode",
    )
    parse = WhitespaceParser()

    def __init__(self, address_name_number=None, address_postcode=None):
        super().__init__(
            address_postcode=address_postcode,
            address_name_number=address_name_number,
        )

    def classify(self, record) -> Collection | None:
        date_str, type_str = record
        cleaned = type_str.replace(" Collection", "").replace(" Service", "").strip()
        try:
            date = self.parse_date(date_str)
        except ValueError:
            _LOGGER.info("Skipped %s: unexpected date format", date_str)
            return None
        return Collection(
            date=date,
            waste_type=_TYPE_MAP.get(cleaned) or resolve(cleaned) or preserved(cleaned),
        )
