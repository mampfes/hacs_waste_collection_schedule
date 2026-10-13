from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import Compose, ExplodeList
from waste_collection_schedule.service.BristolAlloyCalendar import (
    calendar_retriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Bristol City Council"
    DESCRIPTION = "Source for bristol.gov.uk services for Bristol City Council, UK."
    URL = "https://bristol.gov.uk"
    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "107652"},
        "Test_002": {"uprn": "2987"},
        "Test_003": {"uprn": 17929},
    }
    COUNTRY = "uk"
    PARAMS = (uprn(),)

    retrieve = calendar_retriever
    parse = parsers.JsonParser("data")
    preprocess = Compose(
        ExplodeList("collection", into="collection"),
        ExplodeList(
            lambda record, _: [
                record["collection"][key]
                for key in ("nextCollectionDate", "lastCollectionDate")
            ],
            into="date",
        ),
    )
    transform = JsonTransformer(
        date_key="date",
        type_key="containerName",
        parse_date=lambda *values: date_parsers.for_format("%Y-%m-%d")(
            values[-1].split("T")[0]
        ),
        type_value_map={
            "90L BLUE SACK": wt.RECYCLABLES,
            "90L Blue Bag": wt.RECYCLABLES,
            "90L Red Bag": wt.RECYCLABLES,
            "240L GARDEN WASTE BIN": wt.GARDEN_WASTE,
            "180L GENERAL WASTE": wt.GENERAL_WASTE,
            "45L BLACK RECYCLING BOX": wt.RECYCLABLES,
            "23L FOOD WASTE BIN": wt.FOOD_WASTE,
            "55L GREEN RECYCLING BOX": wt.RECYCLABLES,
            "140L FOOD WASTE BIN": wt.FOOD_WASTE,
            "240L RECYCLING MIXED GLASS": wt.GLASS,
            "240L RECYCLING PAPER": wt.PAPER,
            "1100L GENERAL WASTE": wt.GENERAL_WASTE,
            "1100L RECYCLING CARD": wt.PAPER,
            "360L RECYCLING PLASTIC/CANS": [wt.PLASTIC, wt.METAL],
        },
    )
