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

_API_URL = "https://vatjanst.lerum.se/FutureWeb/SimpleWastePickup"


@final
class Source(BaseSource):
    TITLE = "Lerum Vatten och Avlopp"
    DESCRIPTION = "Source for Lerum Vatten och Avlopp waste collection."
    URL = "https://vatjanst.lerum.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "PRO": {"street_address": "Floda stationsväg 5, Floda"},
        "Polisen": {"street_address": "Göteborgsvägen 16, Lerum"},
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
