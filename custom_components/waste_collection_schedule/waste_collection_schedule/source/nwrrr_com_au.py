from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, municipality
from waste_collection_schedule.service.NorthWestTasmaniaCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "North West Resource Recovery and Recycling"
    DESCRIPTION = "Source for North West Resource Recovery and Recycling (NWRRR), serving 8 councils in north-west Tasmania, Australia."
    URL = "https://www.nwrrr.com.au"
    COUNTRY = "au"
    TEST_CASES: ClassVar[dict] = {
        "Devonport (Thursday)": {
            "municipality": "Devonport",
            "region": "Devonport (Thursday)",
        },
        "Strahan (West Coast)": {"municipality": "West Coast", "region": "Strahan"},
        "Smithton East (Circular Head)": {
            "municipality": "Circular Head",
            "region": "Smithton East",
        },
        "Hawley/Shearwater (Latrobe)": {
            "municipality": "Latrobe",
            "region": "Hawley/Shearwater",
        },
    }
    HOWTO: ClassVar[dict] = {
        "en": "Visit https://www.nwrrr.com.au/map, click 'Select Location', then choose your council and region from the list. Use the displayed council name as 'municipality' and the region name as 'region'."
    }
    PARAMS = (
        municipality(),
        district("region"),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "FOGO": wt.ORGANIC,
        },
    )
