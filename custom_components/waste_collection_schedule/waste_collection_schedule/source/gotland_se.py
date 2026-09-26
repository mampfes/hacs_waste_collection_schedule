from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.EdpFutureWeb import (
    TYPE_VALUE_MAP,
    EdpFutureWebParser,
    EdpFutureWebRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://edpfuture.gotland.se/FutureWeb/SimpleWastePickup"


@final
class Source(BaseSource):
    TITLE = "Region Gotland"
    DESCRIPTION = "Source for Region Gotland waste collection."
    URL = "https://gotland.se"
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
        "Adelsgatan 10, Visby": {"uprn": "0106633415"},
        "Hamngatan 1, Visby": {"uprn": "0107806309"},
    }

    PARAMS = (text_field("uprn", "Building ID"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search your address at https://edpfuture.gotland.se/FutureWeb/"
            "SimpleWastePickup and use the number in brackets as 'uprn'."
        ),
    }

    retrieve = EdpFutureWebRetriever(_API_URL, address=None, building_id="uprn")
    parse = EdpFutureWebParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        carry_raw_label=True,
    )
