import logging
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

_LOGGER = logging.getLogger(__name__)

# Deprecated alias for edpevent_se's "ssam" provider, kept so existing
# configurations keep working.
_API_URL = "https://edpfuture.ssam.se/FutureWeb/SimpleWastePickup"


@final
class Source(BaseSource):
    TITLE = "SSAM (Deprecated)"
    DESCRIPTION = "Deprecated, please use edpevent_se instead."
    URL = "https://ssam.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.OTHER, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Home": {"street_address": "Asteroidvägen 1, Växjö"},
        "Långa Gatan 4": {"street_address": "Långa Gatan 4, Växjö"},
        "Slambrunn": {"street_address": "Svanebro Ormesberga, Ör"},
    }

    PARAMS = (street_address("street_address"),)

    retrieve = EdpFutureWebRetriever(_API_URL, address="street_address")
    parse = EdpFutureWebParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        carry_raw_label=True,
    )

    def __init__(self, street_address: str):
        _LOGGER.warning(
            "The SSAM source is deprecated, please use edpevent_se instead."
        )
        super().__init__(street_address=street_address)
