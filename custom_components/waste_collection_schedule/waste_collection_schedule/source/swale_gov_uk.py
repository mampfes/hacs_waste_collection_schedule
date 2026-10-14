from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.SwaleCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Swale Borough Council"
    DESCRIPTION = "Source for swale.gov.uk services for Swale, UK."
    URL = "https://swale.gov.uk"
    TEST_CASES: ClassVar[dict] = {
        "Swale House": {"uprn": 100062375927, "postcode": "ME10 3HT"},
        "1 Harrier Drive": {"uprn": 100061091726, "postcode": "ME10 4UY"},
        "garden waste test": {"uprn": "200002536346", "postcode": "ME10 1YQ"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details."
    }
    COUNTRY = "uk"
    PARAMS = (
        uprn(),
        postcode(),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food": wt.FOOD_WASTE,
            "Garden": wt.GARDEN_WASTE,
        },
    )
