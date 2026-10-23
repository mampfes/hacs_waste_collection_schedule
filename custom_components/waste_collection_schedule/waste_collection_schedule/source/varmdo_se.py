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

_API_URL = "https://edp-futureweb.varmdo.se/FutureWeb/SimpleWastePickup"


@final
class Source(BaseSource):
    TITLE = "Värmdö Sophämtning"
    DESCRIPTION = "Source for Värmdö household waste collection."
    URL = "https://www.varmdo.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rosenmalmsvägen": {"street_address": "Rosenmalmsvägen"},
        "Abborrberget": {"street_address": "Abborrberget"},
        "Idskäret": {"street_address": "Idskäret"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"street_address": "Ingen gata 999"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as shown in the Värmdö kommun address "
            "search, ideally with the house number."
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
