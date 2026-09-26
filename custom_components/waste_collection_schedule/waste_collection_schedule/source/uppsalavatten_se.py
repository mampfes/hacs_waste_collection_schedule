import logging
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.service.EdpFutureWeb import (
    TYPE_VALUE_MAP,
    EdpFutureWebParser,
    EdpFutureWebRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

_LOGGER = logging.getLogger(__name__)

# Deprecated alias for edpevent_se's "uppsalavatten" provider, kept so existing
# configurations keep working.
_API_URL = "https://futureweb.uppsalavatten.se/Uppsala/FutureWeb/SimpleWastePickup"


@final
class Source(BaseSource):
    TITLE = "Uppsala Vatten och Avfall AB (Deprecated)"
    DESCRIPTION = "Deprecated, please use edpevent_se instead."
    URL = "https://www.uppsalavatten.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.OTHER, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Test1": {"city": "BJÖRKLINGE", "street": "SADELVÄGEN 1"},
        "Test2": {"city": "BJÖRKLINGE", "street": "BJÖRKLINGE-GRÄNBY 33"},
        "Test3": {"city": "BJÖRKLINGE", "street": "BJÖRKLINGE-GRÄNBY 20"},
    }

    PARAMS = (
        street(),
        # never used: the street alone finds the address
        city(optional=True),
    )

    retrieve = EdpFutureWebRetriever(_API_URL, address="street")
    parse = EdpFutureWebParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        carry_raw_label=True,
    )

    def __init__(self, street: str, city: str | None = None):
        _LOGGER.warning(
            "The Uppsala Vatten och Avfall AB source is deprecated, please use edpevent_se instead"
        )
        super().__init__(street=street, city=city)
