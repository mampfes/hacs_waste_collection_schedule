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

_API_URL = "https://eservice431601.lund.se/Lund/FutureWeb/SimpleWastePickup"


@final
class Source(BaseSource):
    TITLE = "Lund Waste Collection"
    DESCRIPTION = "Source for Lund waste collection services, Sweden."
    URL = "https://eservice431601.lund.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Lokföraregatan 7": {"street_address": "Lokföraregatan 7, LUND (19120)"},
        "Stora Södergatan 10": {"street_address": "Stora Södergatan 10, LUND (26232)"},
        "Search without id": {"street_address": "Lokföraregatan 7"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"street_address": "Ingen gata 999"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as the provider's own address search lists "
            "it; the building id in brackets, e.g. 'Lokföraregatan 7, LUND "
            "(19120)', skips the search."
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
