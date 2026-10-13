from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    Deduplicate,
    RecurrenceExpander,
)
from waste_collection_schedule.service.WaikatoCollectionCalendar import (
    CalendarParser,
    calendar_retriever,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Waikato District Council"
    DESCRIPTION = "Source for Waikato District Council kerbside rubbish and recycling collection, New Zealand."
    URL = "https://www.waikatodistrict.govt.nz/"
    COUNTRY = "nz"
    TEST_CASES: ClassVar[dict] = {
        "Rotowaro, Monday": {"address": "42B Mahuta Station Road, Rotowaro"},
        "Raglan, Tuesday": {"address": "90 Upper Wainui Road, Raglan"},
        "Tuakau, Tuesday": {"address": "11 Gordon Paul Place, Tuakau"},
        "Pokeno, Thursday": {"address": "53 Market Street, Pokeno"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "Enter your address as it appears on the council's rubbish and recycling collection page, e.g. '18 Example Drive, Huntly'. If the address cannot be found uniquely, the error message will list the closest matches known to the council."
    }
    PARAMS = (street_address(),)

    retrieve = calendar_retriever
    parse = CalendarParser()
    preprocess = Compose(
        RecurrenceExpander(lambda schedule, _: (schedule,)), Deduplicate()
    )
    transform = RowTransformer(
        type_value_map={
            "Rubbish and Recycling": [wt.GENERAL_WASTE, wt.RECYCLABLES],
        },
    )
