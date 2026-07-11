from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import RECYCLABLES

_BASE_URL = "https://www.fritzens.gv.at"


@final
class Source(BaseSource):
    TITLE = "Fritzens"
    DESCRIPTION = "Waste collection schedule for the municipality of Fritzens, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "TestSource": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "blnr": "",
            "gnr_search": "0",
            "menuonr": "219029364",
        },
    )
    parse = RiSKommunalParser()

    # Biomüll, Restmüll and Sperrmüll auto-resolve via the shared vocabulary;
    # Kunststoffmüll has no canonical alias and is mapped explicitly to the
    # equivalent RECYCLABLES type (matching the legacy Icons.PLASTIC_PACKAGING
    # classification).
    transform = ICSTransformer(
        type_value_map={
            "Kunststoffmüll": RECYCLABLES,
        },
    )
