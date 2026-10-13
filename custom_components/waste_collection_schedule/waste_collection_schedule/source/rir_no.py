from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.RirCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "RIR"
    DESCRIPTION = "Source for RIR (Romsdalshalvøya Interkommunale Renovasjonsselskap), serving the municipalities of Aukra, Hustadvika, Gjemnes, Molde and Rauma, Norway."
    URL = "https://www.rir.no"
    COUNTRY = "no"
    TEST_CASES: ClassVar[dict] = {
        "Øvre veg 10C, Molde": {"address": "Øvre veg 10C, Molde"},
        "Årøsetervegen 56, Molde": {"address": "Årøsetervegen 56, Molde"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "Visit https://www.rir.no/hentekalender, start typing your address in the search field, and copy the suggested address exactly (including the postal town) into the 'address' argument."
    }
    PARAMS = (street_address(),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Papir": wt.PAPER,
            "Papp": wt.PAPER,
            "Papp, papir og kartong": wt.PAPER,
            "Plastemballasje": wt.PLASTIC,
            "Glassemballasje": wt.GLASS,
            "Metallemballasje": wt.METAL,
            "Glass- og metallemballasje": [wt.GLASS, wt.METAL],
            "Hageavfall": wt.GARDEN_WASTE,
            "Farlig avfall": wt.HAZARDOUS,
            "Batteri": wt.HAZARDOUS,
            "Trevirke": wt.GENERAL_WASTE,
            "Klær og sko": wt.TEXTILES,
            "Elektrisk og elektronisk": wt.ELECTRONICS,
        },
    )
