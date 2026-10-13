from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address, text_field
from waste_collection_schedule.field_terms import POSTCODE, UPRN
from waste_collection_schedule.service.AdurWorthingCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Adur & Worthing Councils"
    DESCRIPTION = "Source for adur-worthing.gov.uk services for Adur & Worthing, UK."
    URL = "https://adur-worthing.gov.uk"
    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "BN15 9UX", "address": "1 Western Road North"},
        "Test_002": {"postcode": "BN43 5WE", "address": "6 Hebe Road"},
        "Test_003": {"uprn": "100062209109"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details"
    }
    COUNTRY = "uk"
    PARAMS = (
        text_field("postcode", term=POSTCODE, optional=True),
        street_address(optional=True),
        text_field("uprn", term=UPRN, optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Recycling": wt.RECYCLABLES,
            "Refuse": wt.GENERAL_WASTE,
            "Garden": wt.GARDEN_WASTE,
            "Food waste": wt.FOOD_WASTE,
        },
    )
