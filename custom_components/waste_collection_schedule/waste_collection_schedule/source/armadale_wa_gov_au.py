from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
)
from waste_collection_schedule.service.ArmadaleBinCalendar import (
    CalendarParser,
    calendar_retriever,
    holiday_date,
)
from waste_collection_schedule.transformers import RowTransformer


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

    retrieve = calendar_retriever
    parse = CalendarParser()
    preprocess = Compose(
        RecurrenceExpander(lambda schedule, _: (schedule,)),
        HolidayShift(holiday_date),
    )
    transform = RowTransformer(
        type_value_map={
            "rubbish": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
        },
    )
