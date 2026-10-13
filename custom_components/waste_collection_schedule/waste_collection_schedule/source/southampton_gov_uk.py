from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.SouthamptonCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Southampton City Council"
    DESCRIPTION = "Source for southampton.gov.uk services for Southampton City Council"
    URL = "https://southampton.gov.uk"
    TEST_CASES: ClassVar[dict] = {
        "UPRN_001": {"uprn": "100060731893"},
        "UPRN_002": {"uprn": 100060685712},
        "UPRN_003": {"uprn": "100060679858"},
        "UPRN_004": {"uprn": 100060703113},
    }
    COUNTRY = "uk"
    PARAMS = (uprn(),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Glass": wt.GLASS,
            "Recycling": wt.RECYCLABLES,
            "General Waste": wt.GENERAL_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
            "Food": wt.FOOD_WASTE,
        },
    )
