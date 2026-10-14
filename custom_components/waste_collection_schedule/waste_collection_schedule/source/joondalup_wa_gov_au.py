from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    district,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.service.JoondalupCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "City of Joondalup"
    DESCRIPTION = "Source for City of Joondalup (WA) waste collection."
    URL = "https://www.joondalup.wa.gov.au"
    TEST_CASES: ClassVar[dict] = {
        "test address": {
            "number": "2",
            "street": "Ashburton Drive",
            "suburb": "Heathridge",
        },
        "test mapkey": {"mapkey": 785},
        "abbreviated street type": {
            "number": "2",
            "street": "Ashburton Dr",
            "suburb": "Heathridge",
        },
    }
    HOWTO: ClassVar[dict] = {
        "en": "Your house number, street name, and suburb as they appear when searching for your collection schedule on the Joonalup website: https://www.joondalup.wa.gov.au/residents/waste-and-recycling/residential-bin-collections. Alternatively, you can use your mapkey, if you know it."
    }
    COUNTRY = "au"
    PARAMS = (
        house_number("number", optional=True),
        street(optional=True),
        district("suburb", optional=True),
        text_field("mapkey", "Property identifier", optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Recycling": wt.RECYCLABLES,
            "Bulk Put Out": wt.BULKY_WASTE,
            "Bulk Pick Up": wt.BULKY_WASTE,
            "General Waste": wt.GENERAL_WASTE,
            "Green Waste": wt.GARDEN_WASTE,
        },
    )
