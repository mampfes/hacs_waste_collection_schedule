from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.WiganNeighbourhoodCalendar import (
    CalendarRetriever,
    collection_date,
)
from waste_collection_schedule.transformers import RowTransformer


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
    parse = parsers.HtmlLabelledDates(
        "div.BinsRecycling",
        label="h2",
        date="div.dateWrapper-next",
        date_pattern=r"day(.*)",
    )
    transform = RowTransformer(
        parse_date=collection_date,
        type_value_map={
            "BLACK BIN": wt.GENERAL_WASTE,
            "BROWN BIN": wt.ORGANIC,
            "GREEN BIN": wt.GARDEN_WASTE,
            "BLUE BIN": wt.RECYCLABLES,
        },
    )
