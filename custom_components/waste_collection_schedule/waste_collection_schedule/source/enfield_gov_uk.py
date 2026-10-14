from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address, text_field
from waste_collection_schedule.field_terms import UPRN
from waste_collection_schedule.service.EnfieldCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Enfield Council"
    DESCRIPTION = "Source for Enfield Council, London, UK."
    URL = "https://www.enfield.gov.uk/services/rubbish-and-recycling/find-my-collection-day"
    COUNTRY = "uk"
    TEST_CASES: ClassVar[dict] = {
        "uprn": {"uprn": "207102166"},
        "address": {"address": "127 Palmerston Rd, London N22 8QX"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "Search for your address on the Enfield Council collection-day page. If address lookup is ambiguous, use your UPRN from [Find My Address](https://www.findmyaddress.co.uk/)."
    }
    PARAMS = (
        text_field("uprn", term=UPRN, optional=True),
        street_address(optional=True),
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
