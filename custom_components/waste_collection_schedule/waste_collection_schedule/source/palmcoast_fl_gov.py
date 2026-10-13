from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.service.PalmCoastCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Palm Coast, FL"
    DESCRIPTION = "Source for Palm Coast, FL waste collection."
    URL = "https://www.palmcoast.gov"
    COUNTRY = "us"
    TEST_CASES: ClassVar[dict] = {"Ripcord Lane": {"street": "Ripcord Lane"}}
    PARAMS = (street(),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Yard Waste": wt.GARDEN_WASTE,
            "Recycling": wt.RECYCLABLES,
        },
    )
