from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.service.BarrieCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "City of Barrie"
    DESCRIPTION = "Source for City of Barrie, Ontario, Canada."
    URL = "https://www.barrie.ca/services-payments/garbage-recycling-organics/curbside-collection/collection-schedules"
    COUNTRY = "ca"
    TEST_CASES: ClassVar[dict] = {
        "Quance St": {"street_number": "47", "street_name": "Quance St"},
        "Kozlov St": {"street_number": "100", "street_name": "Kozlov St"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "Enter your street number and street name as shown on the [Barrie collection schedule page](https://www.barrie.ca/services-payments/garbage-recycling-organics/curbside-collection/collection-schedules). Abbreviate street suffixes (e.g. 'St' not 'Street', 'Ave' not 'Avenue')."
    }
    PARAMS = (
        house_number("street_number"),
        street("street_name"),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Organics": wt.ORGANIC,
            "Yard Waste": wt.GARDEN_WASTE,
            "Textile Collection": wt.TEXTILES,
            "Battery Collection": wt.HAZARDOUS,
            "Christmas Tree": wt.GARDEN_WASTE,
        },
    )
