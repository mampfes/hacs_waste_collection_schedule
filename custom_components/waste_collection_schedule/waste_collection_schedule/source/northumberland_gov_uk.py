from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.NorthumberlandCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Northumberland County Council"
    DESCRIPTION = "Source for Northumberland County Council waste collection schedule."
    URL = "https://www.northumberland.gov.uk"
    COUNTRY = "uk"
    TEST_CASES: ClassVar[dict] = {
        "30, NE46 1UF (UPRN 100110637553)": {
            "uprn": "100110637553",
            "postcode": "NE46 1UF",
        }
    }
    HOWTO: ClassVar[dict] = {
        "en": "Visit https://bincollection.northumberland.gov.uk/postcode, enter your postcode and select your address. The UPRN is the number in the address dropdown (or find it at https://www.findmyaddress.co.uk/)."
    }
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
            "General Waste": wt.GENERAL_WASTE,
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
            "Food Waste": wt.FOOD_WASTE,
            "Glass": wt.GLASS,
        },
    )
