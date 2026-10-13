from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.GoldenPlainsCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Golden Plains Shire Council"
    URL = "https://www.goldenplains.vic.gov.au"
    DESCRIPTION = "Source for Golden Plains Shire Council, VIC, AU"
    COUNTRY = "au"
    TEST_CASES: ClassVar[dict] = {
        "2 Pope Street Bannockburn": {"address": "2 POPE STREET BANNOCKBURN 3331"}
    }
    PARAMS = (street_address(),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Recycling": wt.RECYCLABLES,
            "Garbage": wt.GENERAL_WASTE,
            "Glass": wt.GLASS,
        },
    )
