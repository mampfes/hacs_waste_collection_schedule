from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.RfdCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Renovasjonsselskapet for Drammensregionen IKS (RfD)"
    DESCRIPTION = "Source for RfD waste collection schedules"
    URL = "https://www.rfd.no"
    COUNTRY = "no"
    TEST_CASES: ClassVar[dict] = {
        "Bragernes Torg 13": {"address": "Bragernes Torg 13, Drammen"}
    }
    HOWTO: ClassVar[dict] = {
        "en": "Search for your address at rfd.no/avfallshenting. Use the address exactly as shown in the result list, for example 'Bragernes Torg 13, Drammen'."
    }
    PARAMS = (street_address(),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Mat- og restavfall": [wt.GENERAL_WASTE, wt.FOOD_WASTE],
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Papiravfall": wt.PAPER,
            "Glass- og metallemballasje": [wt.GLASS, wt.METAL],
            "Hageavfall": wt.GARDEN_WASTE,
            "Plastemballasje": wt.PLASTIC,
        },
    )
