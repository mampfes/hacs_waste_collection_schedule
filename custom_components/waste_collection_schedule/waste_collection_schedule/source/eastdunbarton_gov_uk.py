from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer


def _text(row: Tag, selector: str) -> str:
    # A missing cell raises, which HtmlTransformer turns into a skipped row.
    cell = row.select_one(selector)
    if cell is None:
        raise AttributeError(f"no cell matching {selector!r}")
    return cell.get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "East Dunbartonshire Council"
    DESCRIPTION = "Source for East Dunbartonshire Council, UK."
    URL = "https://eastdunbarton.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "132020996"},
        "Test_002": {"uprn": 132040577},
        "Test_003": {"uprn": 132020494},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url=(
            "https://www.eastdunbarton.gov.uk/services/a-z-of-services/"
            "bins-waste-and-recycling/bins-and-recycling/collections/"
        ),
        params=lambda uprn, **_: {"uprn": uprn},
    )
    parse = parsers.HtmlParser("tr:has(span)")
    # "Monday, 28 September 2026"
    transform = HtmlTransformer(
        date_getter=lambda row: _text(row, "td span").split(", ")[1],
        type_getter=lambda row: _text(row, "td"),
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map={
            "Grey bin": wt.GENERAL_WASTE,
            "Blue bin": wt.RECYCLABLES,
            "Green bin": wt.ORGANIC,
            "Food caddy": wt.FOOD_WASTE,
            "Brown bin": wt.GARDEN_WASTE,
        },
    )
