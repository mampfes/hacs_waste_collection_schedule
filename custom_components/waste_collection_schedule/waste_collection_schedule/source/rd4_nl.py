from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.preprocessors import FlattenGroups
from waste_collection_schedule.transformers import JsonTransformer


def _calendar_query(
    year: int,
    _context,
    postal_code: str,
    house_number,
    house_number_extension=None,
    **_,
) -> dict:
    """One year's calendar for the address."""
    query = {
        "postal_code": postal_code,
        "house_number": house_number,
        "year": year,
    }
    if house_number_extension:
        query["house_number_extension"] = house_number_extension
    return query


@final
class Source(BaseSource):
    TITLE = "Rd4"
    DESCRIPTION = "Source for Rd4."
    URL = "https://rd4.nl/"
    COUNTRY = "nl"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "6417 AT 32": {"postal_code": "6417 AT", "house_number": 32}
    }

    PARAMS = (
        postcode("postal_code", "house_number"),
        text_field("house_number_extension", "House Number Extension", optional=True),
    )

    # The calendar is published per year; December also asks for next year.
    retrieve = retrievers.YearlyRetriever(
        fetch=retrievers.Request(
            "https://data.rd4.nl/api/v1/waste-calendar",
            params=_calendar_query,
        ),
    )
    # ``items`` holds one list of collections per month. Next year's calendar
    # may not be published yet in December.
    parse = parsers.EachResponse(
        parsers.JsonParser("data", "items"), skip_failures=True
    )
    preprocess = FlattenGroups()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "pmd": wt.RECYCLABLES,
            "gft": wt.ORGANIC,
            "residual_waste": wt.GENERAL_WASTE,
            "paper": wt.PAPER,
            "pruning_waste": wt.GARDEN_WASTE,
            "best_bag": wt.OTHER,
            "christmas_trees": wt.GARDEN_WASTE,
        },
    )
