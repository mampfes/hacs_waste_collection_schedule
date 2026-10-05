from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer


def _date(term) -> str:
    # The dd after each dt holds a <time datetime="YYYY-MM-DD">; a dd without
    # one (the bulky-item service's description) raises and skips the row.
    return term.find_next_sibling("dd").select_one("time")["datetime"]


@final
class Source(BaseSource):
    TITLE = "Eastleigh Borough Council"
    DESCRIPTION = "Source for Eastleigh Borough Council."
    URL = "https://eastleigh.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GLASS,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "100060319000": {"uprn": 100060319000},
        "100060300958": {"uprn": "100060300958"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url=(
            "https://eastleigh.gov.uk/waste-bins-and-recycling/collection-dates/"
            "your-waste-bin-and-recycling-collections"
        ),
        params=lambda uprn, **_: {"uprn": uprn},
    )
    parse = parsers.HtmlParser("dl dt")
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=lambda term: term.get_text(strip=True),
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Household Waste Bin": wt.GENERAL_WASTE,
            "Recycling Bin": wt.RECYCLABLES,
            "Food Waste Bin": wt.FOOD_WASTE,
            "Glass Box and Batteries": wt.GLASS,
            "Garden Waste Bin": wt.GARDEN_WASTE,
        },
    )
