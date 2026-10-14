from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, text_field
from waste_collection_schedule.field_terms import POSTCODE, UPRN
from waste_collection_schedule.service.LewishamCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "London Borough of Lewisham"
    DESCRIPTION = "Source for services from the London Borough of Lewisham"
    URL = "https://lewisham.gov.uk"
    TEST_CASES: ClassVar[dict] = {
        "houseNumber": {"post_code": "SE41LR", "number": 4},
        "houseName": {"post_code": "SE233TE", "name": "The Haven"},
        "houseUprn": {"uprn": "10070495030"},
        "houseUprn2": {"uprn": 100021959032},
    }
    COUNTRY = "uk"
    PARAMS = (
        text_field("post_code", term=POSTCODE, optional=True),
        house_number("number", optional=True),
        text_field("name", "Property name", optional=True),
        text_field("uprn", term=UPRN, optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food waste": wt.FOOD_WASTE,
            "Garden waste": wt.GARDEN_WASTE,
        },
    )
