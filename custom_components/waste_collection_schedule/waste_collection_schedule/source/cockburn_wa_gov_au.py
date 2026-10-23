from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address, text_field
from waste_collection_schedule.service.CockburnCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "City of Cockburn"
    DESCRIPTION = "Source script for cockburn.wa.gov.au"
    URL = "https://www.cockburn.wa.gov.au"
    TEST_CASES: ClassVar[dict] = {
        "Thursday": {"address": "23 Snowden St, Hammond Park WA 6164"},
        "Friday": {"address": "1 Eucalyptus Dr Hammond Park"},
        "Postcode without state": {"address": "23 Snowden Street HAMMOND PARK 6164"},
        "Tuesday int": {"property_no": 6025742},
        "Tuesday str": {"property_no": "6025742"},
    }
    COUNTRY = "au"
    PARAMS = (
        street_address(optional=True),
        text_field("property_no", "Property number", optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Junk Waste": wt.BULKY_WASTE,
            "Green Waste": wt.GARDEN_WASTE,
            "Green Bin": wt.ORGANIC,
        },
    )
