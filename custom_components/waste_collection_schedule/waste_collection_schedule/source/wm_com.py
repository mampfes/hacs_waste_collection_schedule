from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, postcode, street, text_field
from waste_collection_schedule.service.WasteManagementCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Waste Management (WM)"
    DESCRIPTION = "Source for Waste Management (wm.com) residential pickup schedules using the guest address lookup — no account required."
    URL = "https://www.wm.com"
    COUNTRY = "us"
    TEST_CASES: ClassVar[dict] = {
        "Example Address": {
            "street": "245 Emerson Ave",
            "city": "Ypsilanti",
            "state": "MI",
            "zip_code": "48198",
        }
    }
    PARAMS = (
        street(),
        city(),
        text_field("state", "State"),
        postcode("zip_code"),
        text_field("country", "Service country", default="US"),
    )
    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "GARBAGE": wt.GENERAL_WASTE,
            "MSW": wt.GENERAL_WASTE,
            "RECYCLABLE": wt.RECYCLABLES,
            "YARD_WASTE": wt.GARDEN_WASTE,
            "BULK": wt.BULKY_WASTE,
        },
    )
