from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street, text_field
from waste_collection_schedule.service.OloCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "OLO"
    DESCRIPTION = "Source for OLO in Bratislava, Slovakia"
    URL = "https://www.olo.sk"
    TEST_CASES: ClassVar[dict] = {
        "ByRegistrationNumber": {"registrationNumber": "1353013"},
        "ByStreet": {"street": "Jantarova 47"},
    }
    COUNTRY = "sk"
    PARAMS = (
        street(optional=True),
        text_field("registrationNumber", "Registration number", optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Zmesový komunálny odpad": wt.GENERAL_WASTE,
            "Kuchynský bioodpad": wt.FOOD_WASTE,
            "Záhradný bioodpad": wt.GARDEN_WASTE,
            "Plast, kovy a nápojové kartóny": [wt.PLASTIC, wt.METAL, wt.CARTONS],
            "Papier": wt.PAPER,
            "Sklo": wt.GLASS,
        },
    )
