from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.service.CalendarDataApi import (
    PARSE_DATE,
    calendar_data_parser,
    calendar_data_retriever,
    scheduled_date,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Sheffield City Council"
    DESCRIPTION = (
        "Source for waste collection services from Sheffield City Council (SCC)"
    )
    URL = "https://sheffield.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "test001": {"uprn": 100050938234},
        "test002": {"uprn": 100050961380},
        "test003": {"uprn": "100050920796"},
        "test004": {"uprn": "100051085306"},
    }

    PARAMS = (uprn(),)

    retrieve = calendar_data_retriever("https://wasteservices.sheffield.gov.uk", "1")
    parse = calendar_data_parser()
    preprocess = ExplodeList("records")
    transform = JsonTransformer(
        date_key=scheduled_date,
        type_key="service",
        parse_date=PARSE_DATE,
        type_value_map={
            "Black Bin": wt.GENERAL_WASTE,
            "Blue Bin": wt.PAPER,
            "Brown Bin": wt.RECYCLABLES,
            "Green Bin": wt.GARDEN_WASTE,
        },
    )
