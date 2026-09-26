from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.EdpFutureWeb import (
    TYPE_VALUE_MAP,
    EdpFutureWebParser,
    EdpFutureWebRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://minasidor.juneavfall.se/FutureWebJuneBasic/SimpleWastePickup"


@final
class Source(BaseSource):
    TITLE = "Jönköping - June Avfall & Miljö"
    DESCRIPTION = "Source for June Avfall & Miljö waste collection."
    URL = "https://www.juneavfall.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.OTHER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Storgatan 12": {"street_address": "Storgatan 12, Huskvarna"},
        "Smedjegatan 1": {"street_address": "Smedjegatan 1, Jönköping"},
        "Västra Ubbarp 20": {"street_address": "Västra Ubbarp 20, Jönköping"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"street_address": "Ingen gata 999"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as the provider's own address search lists "
            "it, including the locality."
        ),
    }

    retrieve = EdpFutureWebRetriever(_API_URL)
    parse = EdpFutureWebParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        carry_raw_label=True,
    )
