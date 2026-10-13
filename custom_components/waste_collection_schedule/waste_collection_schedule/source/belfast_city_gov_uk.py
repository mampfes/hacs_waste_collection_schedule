from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.field_terms import UPRN
from waste_collection_schedule.service.BelfastBinCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Belfast City Council"
    DESCRIPTION = "Source for belfastcity.gov.uk waste collection services."
    URL = "https://online.belfastcity.gov.uk/find-bin-collection-day"
    TEST_CASES: ClassVar[dict] = {
        "Test_1": {"postcode": "BT9 6DG", "uprn": "185075148"},
        "Test_2": {"postcode": "BT9 6DG"},
    }
    COUNTRY = "uk"
    PARAMS = (
        postcode(),
        text_field("uprn", term=UPRN, optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Recycling bin": wt.RECYCLABLES,
            "Compost bin": wt.ORGANIC,
            "General waste bin": wt.GENERAL_WASTE,
        },
    )
