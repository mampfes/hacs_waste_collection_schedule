from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field, uprn
from waste_collection_schedule.field_terms import POSTCODE
from waste_collection_schedule.preprocessors import (
    Compose,
    DateFields,
    DefaultPreprocessor,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

_parse = date_parsers.for_format("%Y-%m-%d")


def _next_date(stream):
    """The next date of one stream ({"nextCollectionDate": "2026-09-29T01:00:00.000Z"})."""
    value = (stream or {}).get("nextCollectionDate")
    return _parse(value[:10]) if value else None


@final
class Source(BaseSource):
    TITLE = "Tewkesbury Borough Council"
    DESCRIPTION = "Home waste collection schedule for Tewkesbury Borough Council"
    URL = "https://www.tewkesbury.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "UPRN example": {"uprn": 100120544973},
    }

    PARAMS = (uprn(), text_field("postcode", term=POSTCODE, optional=True))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your UPRN; you can look it up on https://www.findmyaddress.co.uk/. "
            "The postcode is no longer used: the council retired the postcode lookup."
        ),
    }

    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: (
            f"https://api-2.tewkesbury.gov.uk/incab/rounds/{uprn}/next-collection"
        ),
    )
    parse = parsers.JsonParser()
    preprocess = Compose(
        DefaultPreprocessor(),
        DateFields(
            fields={
                "refuse": "Refuse",
                "recycling": "Recycling",
                "food": "Food",
                "garden": "Garden",
            },
            parse_date=_next_date,
        ),
    )
    transform = ICSTransformer(
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food": wt.FOOD_WASTE,
            "Garden": wt.GARDEN_WASTE,
        }
    )
