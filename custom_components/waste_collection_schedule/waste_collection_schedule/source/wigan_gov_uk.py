from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.WiganNeighbourhoodCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Wigan Council"
    DESCRIPTION = "Source for wigan.gov.uk services for Wigan Council, UK."
    URL = "https://wigan.gov.uk"
    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "WN5 9BH", "uprn": "100011821616"},
        "Test_002": {"postcode": "WN6 8RG", "uprn": "100011776859"},
        "Test_003": {"postcode": "wn36au", "uprn": 100011749007},
    }
    COUNTRY = "uk"
    PARAMS = (
        postcode(),
        uprn(),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "BLACK BIN": wt.GENERAL_WASTE,
            "BROWN BIN": wt.ORGANIC,
            "GREEN BIN": wt.GARDEN_WASTE,
            "BLUE BIN": wt.RECYCLABLES,
        },
    )
