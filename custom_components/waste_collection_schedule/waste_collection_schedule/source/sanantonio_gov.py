from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.SanAntonioCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "City of San Antonio"
    DESCRIPTION = "Source for City of San Antonio, Texas waste collection."
    URL = "https://www.sa.gov/Directory/Departments/SWMD/Garbage/My-Collection-Day"
    COUNTRY = "us"
    TEST_CASES: ClassVar[dict] = {
        "H-E-B Corporate Office Headquarters": {"address": "646 S Flores St"},
        "Freeman Coliseum": {"address": "3201 E Houston St"},
        "Witte Museum": {"address": "3801 Broadway"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "The source argument is the street number and street name to the house with waste collection. The address can be tested [here](https://www.sa.gov/Directory/Departments/SWMD/Brush-Bulky/My-Collection-Day)."
    }
    PARAMS = (street_address(),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Recycle": wt.RECYCLABLES,
            "Organics": wt.ORGANIC,
            "Brush": wt.GARDEN_WASTE,
            "Bulky": wt.BULKY_WASTE,
        },
    )
