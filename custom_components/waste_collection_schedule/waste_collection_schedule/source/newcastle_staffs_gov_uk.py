from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer

# One row per date ("Tuesday 29 September", no year) listing its bins as
# lines of the second cell.


@final
class Source(BaseSource):
    TITLE = "Newcastle Under Lyme Borough Council"
    DESCRIPTION = (
        "Source for waste collection services for Newcastle Under Lyme Borough Council"
    )
    URL = "https://www.newcastle-staffs.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": 100031744129},
        "Test_002": {"uprn": "100031726082"},
        "Test_003": {"uprn": 100031736973},
        "Test_004": {"uprn": "200004602766"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.newcastle-staffs.gov.uk/homepage/97/check-your-bin-day",
        params=lambda uprn, **_: {"uprn": uprn},
    )
    parse = parsers.HtmlLabelledDates(
        "tr",
        label="td:nth-of-type(2)",
        date="td:nth-of-type(1)",
        label_separator="\n",
        parse_date=date_parsers.nearest_year("%A %d %B"),
    )
    transform = RowTransformer(
        type_value_map={
            "Household Rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food Waste": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
