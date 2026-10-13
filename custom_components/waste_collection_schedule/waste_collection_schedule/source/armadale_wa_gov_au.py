from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.ArmadaleBinCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Armadale (Western Australia)"
    DESCRIPTION = "Source for Armadale (Western Australia)."
    URL = "https://my.armadale.wa.gov.au"
    TEST_CASES: ClassVar[dict] = {
        "23 Sexty St, ARMADALE": {"address": "23 Sexty St, ARMADALE"},
        "270 Skeet Rd, HARRISDALE": {"address": "270 Skeet Rd, HARRISDALE"},
    }
    COUNTRY = "au"
    PARAMS = (street_address(),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "rubbish": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
        },
    )
