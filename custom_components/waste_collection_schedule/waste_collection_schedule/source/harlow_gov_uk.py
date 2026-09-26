from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import HtmlTransformer

# Demonstrates: HtmlTransformer over the rows of a Firmstep custom page. Each
# collection is one ``div.collectionsrow`` holding an icon, the bin name and a
# "Mon - 28 Sep 2026" date in three sibling cells; the page's other
# ``collectionsrow`` divs (the address picker, an "Please select an address"
# notice) carry no such cells and are skipped by the getters.


def _cell(row: Tag, position: int) -> str:
    cell = row.select_one(f"div:nth-of-type({position})")
    if cell is None:
        raise AttributeError(f"no cell {position}")
    return cell.get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "Harlow Council"
    DESCRIPTION = "Source for harlow.gov.uk, Harlow Council, UK"
    URL = "https://www.harlow.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "12 Kingfisher Gate, Old Harlow": {"uprn": 10033891501},
        "4 Ryecroft, Harlow": {"uprn": 100090544008},
        "2 The Crescent, Harlow": {"uprn": 100090546627},
        "1 Kerril Croft, Harlow": {"uprn": 10003708086},
    }

    PARAMS = (uprn(),)

    retrieve = retrievers.HttpGetRetriever(
        url="https://selfserve.harlow.gov.uk/appshost/firmstep/self/apps/custompage/bincollectionsecho",
        params=lambda uprn, **_: {"uprn": uprn},
    )
    parse = parsers.HtmlParser("div.row.collectionsrow")
    transform = HtmlTransformer(
        date_getter=lambda row: _cell(row, 3),
        type_getter=lambda row: _cell(row, 2),
        parse_date=date_parsers.for_format("%a - %d %b %Y"),
        type_value_map={
            "Non-Recycling": wt.GENERAL_WASTE,
            "Communal Non-Recycling": wt.GENERAL_WASTE,
            "Food Caddy": wt.FOOD_WASTE,
            "Communal Food": wt.FOOD_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Communal Recycling": wt.RECYCLABLES,
            "Green Waste Subscription": wt.GARDEN_WASTE,
        },
    )
