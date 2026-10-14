from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address, text_field
from waste_collection_schedule.service.RepublicServicesCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Republic Services"
    DESCRIPTION = "Source for Republic Services Collection."
    URL = "https://www.republicservices.com"
    COUNTRY = "us"
    TEST_CASES: ClassVar[dict] = {
        "Scott Country Clerk": {
            "street_address": "101 E Main St, Georgetown, KY 40324",
            "method": 1,
        },
        "Branch County Clerk": {
            "street_address": "31 Division St. Coldwater, MI 49036",
            "method": "1",
        },
        "Contract Collection": {
            "street_address": "8957 Park Meadows Dr, Elk Grove, CA 95624",
            "method": 2,
        },
        "Residential Collection": {
            "street_address": "117 Roxie Ln, Georgetown, KY 40324",
            "method": "2",
        },
        "No Method arg": {
            "street_address": "8957 Park Meadows Dr, Elk Grove, CA 95624"
        },
        "4420 Oasis Hill Ave, North Las Vegas, NV 89085": {
            "street_address": "4420 Oasis Hill Ave, North Las Vegas, NV 89085",
            "method": 2,
        },
        "Not Running holiday": {
            "street_address": "700 E Warm Springs Ave, Boise, ID 83712",
            "method": 2,
        },
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "no_pickup_schedule_fizer": {
            "street_address": "104 Fizer Dr, Georgetown, KY 40324",
            "method": 2,
        }
    }
    PARAMS = (
        street_address("street_address"),
        text_field("method", "Classification method", default="1"),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Solid Waste": wt.GENERAL_WASTE,
            "Recycle": wt.RECYCLABLES,
            "Yard Waste": wt.GARDEN_WASTE,
            "Bulk Waste": wt.BULKY_WASTE,
        },
    )
