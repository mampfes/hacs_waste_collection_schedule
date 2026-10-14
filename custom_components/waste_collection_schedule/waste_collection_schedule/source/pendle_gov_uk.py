from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    boolean,
    postcode,
    street_address,
    text_field,
)
from waste_collection_schedule.service.PendleCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Pendle Borough Council"
    DESCRIPTION = "Source for Pendle Borough Council."
    URL = "https://www.pendle.gov.uk/binday"
    TEST_CASES: ClassVar[dict] = {
        "Pendle Market Street": {
            "postcode": "BB9 7LJ",
            "address": "PENDLE LEISURE TRUST, 1, MARKET STREET, NELSON",
        }
    }
    HOWTO: ClassVar[dict] = {
        "en": "Enter the postcode and address as returned by Pendle Borough Council. Set garden_waste_bin to true when the property has a green garden waste bin, and set collection_zone only if Pendle returns multiple schedules for the address."
    }
    COUNTRY = "uk"
    PARAMS = (
        postcode(),
        street_address(),
        text_field("collection_zone", "Collection zone", optional=True),
        boolean("garden_waste_bin", "Garden waste subscription", default=False),
        boolean(
            "future_collection_dates",
            "Expand published collection frequency",
            default=False,
        ),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Domestic refuse": wt.GENERAL_WASTE,
            "Blue Collection": wt.RECYCLABLES,
            "Food Waste Collection": wt.FOOD_WASTE,
            "Food Collection": wt.FOOD_WASTE,
            "Green Collection": wt.GARDEN_WASTE,
            "Grey Collection": wt.GENERAL_WASTE,
            "Brown Collection": wt.ORGANIC,
            "Recycling": wt.RECYCLABLES,
            "Garden waste": wt.GARDEN_WASTE,
        },
    )
