import logging
from typing import final

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.service.WhitespaceWRP import (
    WhitespaceParser,
    WhitespaceRetriever,
)
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
    preserved,
    resolve,
)

# Demonstrates: a fully declarative service-backed source. The Whitespace WRP
# platform's 4-step scrape lives in its service module as WhitespaceRetriever +
# WhitespaceParser, so this source only declares the pipeline and maps the
# council's open-ended type labels onto canonical WasteTypes in classify().

_LOGGER = logging.getLogger(__name__)

_TYPE_MAP = {
    "Domestic Waste": GENERAL_WASTE,
    "Garden Waste": GARDEN_WASTE,
    "Recycling Red": RECYCLABLES,
    "Recycling Yellow": RECYCLABLES,
    "Recycling": RECYCLABLES,
    "Food Waste": FOOD_WASTE,
}
_SUFFIXES = (
    " Collection Service",
    " Collection - refer to calendar for stream",
)


def _clean_collection_type(type_text: str) -> str:
    for suffix in _SUFFIXES:
        if type_text.endswith(suffix):
            return type_text[: -len(suffix)].strip()
    return type_text.strip()


@final
class Source(BaseSource):
    TITLE = "Lancaster City Council"
    DESCRIPTION = "Source for lancaster.gov.uk services for Lancaster City Council, UK."
    URL = "https://lancaster.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES = [GENERAL_WASTE, RECYCLABLES, GARDEN_WASTE, FOOD_WASTE]
    API_URL = "https://lcc-wrp.whitespacews.com"

    TEST_CASES = {
        "1 Queen Street Lancaster, LA1 1RS": {"house_number": 1, "postcode": "LA1 1RS"}
    }

    PARAMS = [postcode(), text_field("house_number", optional=True)]

    HOWTO = {
        "en": "Provide your postcode and house name or number as shown on the "
        "council's bin-day lookup.",
    }

    parse_date = date_parsers.for_format("%d/%m/%Y")

    retrieve = WhitespaceRetriever(name_number="house_number", postcode="postcode")
    parse = WhitespaceParser()

    def __init__(self, postcode: str, house_number: int | str | None = None):
        super().__init__(postcode=postcode, house_number=house_number)

    def classify(self, record) -> Collection | None:
        date_str, type_str = record
        cleaned = _clean_collection_type(type_str)
        label = (
            cleaned
            if cleaned in _TYPE_MAP
            else next((key for key in _TYPE_MAP if type_str.startswith(key)), cleaned)
        )
        try:
            date = self.parse_date(date_str)
        except ValueError:
            _LOGGER.info("Skipped %s: unexpected date format", date_str)
            return None
        return Collection(
            date=date,
            waste_type=_TYPE_MAP.get(label) or resolve(label) or preserved(label),
        )
