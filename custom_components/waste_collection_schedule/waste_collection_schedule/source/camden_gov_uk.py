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
    TITLE = "London Borough of Camden"
    DESCRIPTION = "Source for London Borough of Camden."
    URL = "https://www.camden.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Red Lion Street": {"uprn": 5121151},
    }

    PARAMS = (uprn(),)

    retrieve = calendar_data_retriever(
        "https://recyclingandrubbishcollections.camden.gov.uk", "27"
    )
    parse = calendar_data_parser()
    preprocess = ExplodeList("records")
    transform = JsonTransformer(
        date_key=scheduled_date,
        type_key="service",
        parse_date=PARSE_DATE,
        type_value_map={
            "Rubbish collection": wt.GENERAL_WASTE,
            "Recycling collection": wt.RECYCLABLES,
            "Food collection": wt.FOOD_WASTE,
            "Garden collection": wt.GARDEN_WASTE,
        },
    )
