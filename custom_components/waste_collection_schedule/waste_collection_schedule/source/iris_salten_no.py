from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address, text_field
from waste_collection_schedule.field_terms import MUNICIPALITY
from waste_collection_schedule.service.IrisSaltenCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Iris Salten"
    DESCRIPTION = (
        "Fetches waste collection schedule from Iris Salten (based on address)."
    )
    URL = "https://www.iris-salten.no"
    TEST_CASES: ClassVar[dict] = {
        "My address": {"address": "Alsosgården 11", "kommune": "Bodø kommune"}
    }
    COUNTRY = "no"
    PARAMS = (
        street_address(),
        text_field("kommune", term=MUNICIPALITY, default=""),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Matavfall uten hageavfall": wt.FOOD_WASTE,
            "Papir": wt.PAPER,
            "Papir og papp": wt.PAPER,
            "Plast": wt.PLASTIC,
            "Plastemballasje": wt.PLASTIC,
            "Glass- og metallemballasje": [wt.GLASS, wt.METAL],
            "Glass og metall": [wt.GLASS, wt.METAL],
        },
    )
