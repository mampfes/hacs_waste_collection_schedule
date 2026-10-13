from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import RecurrenceExpander
from waste_collection_schedule.service.HastingsCollectionCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Hastings District Council"
    DESCRIPTION = "Source for Napier City Council"
    URL = "https://www.hastingsdc.govt.nz/"
    COUNTRY = "nz"
    TEST_CASES: ClassVar[dict] = {
        "Test2": {"address": "805 Fitzroy Avenue"},
        "Test3": {"address": "704 Park Road South"},
        "Test4": {"address": "21 Drovers Way"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Ambiguous Heretaunga address": {"address": "200 Heretaunga Street East"}
    }
    PARAMS = (street_address(),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    preprocess = RecurrenceExpander(lambda schedule, _: (schedule,))
    transform = RowTransformer(
        type_value_map={
            "Rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
        },
    )
