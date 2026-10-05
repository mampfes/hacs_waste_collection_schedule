from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "South Staffordshire Council"
    DESCRIPTION = "Source for waste collection services for South Staffordshire Council"
    URL = "https://sstaffs.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100031831923"},
        "Test_002": {"uprn": 100031811736},
        "Test_003": {"uprn": "100031799974"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.sstaffs.gov.uk/where-i-live",
        params=lambda uprn, **_: {"objectId": uprn},
    )
    # The next collection is highlighted above a table of the following ones;
    # both name every round collected that day ("General Waste & Food Waste").
    parse = parsers.HtmlLabelledDates(
        ":has(> p.collection-date), tr:has(td + td)",
        label="p.collection-type, td:nth-of-type(1)",
        date="p.collection-date, td:nth-of-type(2)",
        label_separator="&",
        parse_date=date_parsers.for_format("%A, %d %B %Y"),
    )
    transform = RowTransformer(
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Food Waste": wt.FOOD_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
