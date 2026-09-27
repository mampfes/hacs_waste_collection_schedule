from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer


@final
class Source(BaseSource):
    TITLE = "Runnymede Borough Council"
    DESCRIPTION = "Source Script for www.runnymede.gov.uk services for Runnymede Borough Council, Surrey, UK"
    URL = "https://www.runnymede.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Acacia Close/uprn as string": {"uprn": "100061482004"},
        "Acacia Close/uprn as number": {"uprn": 100061482004},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.runnymede.gov.uk/bin-collection-day",
        params=lambda uprn, **_: {"address": uprn},
    )
    parse = parsers.HtmlParser("tr:has(td + td)")
    transform = HtmlTransformer(
        date_getter=lambda row: row.select("td")[1].get_text(strip=True),
        type_getter=lambda row: row.select("td")[0].get_text(strip=True),
        parse_date=date_parsers.for_format("%A, %d %B %Y"),
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food caddy": wt.FOOD_WASTE,
            "Garden waste": wt.GARDEN_WASTE,
        },
    )
