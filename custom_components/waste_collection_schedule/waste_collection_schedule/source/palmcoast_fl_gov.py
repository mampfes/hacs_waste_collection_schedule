from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.preprocessors import WeekdayRecurrence
from waste_collection_schedule.service.PalmCoastCalendar import (
    CalendarParser,
    calendar_retriever,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Palm Coast, FL"
    DESCRIPTION = "Source for Palm Coast, FL waste collection."
    URL = "https://www.palmcoast.gov"
    COUNTRY = "us"
    TEST_CASES: ClassVar[dict] = {"Ripcord Lane": {"street": "Ripcord Lane"}}
    PARAMS = (street(),)

    retrieve = calendar_retriever
    parse = CalendarParser()
    preprocess = WeekdayRecurrence(
        day={
            "solidWasteDays": "Garbage",
            "yardWasteDays": "Yard Waste",
            "recycleDays": "Recycling",
        },
        separator="/",
        count=26,
    )
    transform = RowTransformer(
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Yard Waste": wt.GARDEN_WASTE,
            "Recycling": wt.RECYCLABLES,
        },
    )
