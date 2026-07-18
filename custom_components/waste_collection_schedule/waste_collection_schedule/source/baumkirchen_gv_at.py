from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import RECYCLABLES

_BASE_URL = "https://www.baumkirchen.gv.at"


@final
class Source(BaseSource):
    TITLE = "Baumkirchen"
    DESCRIPTION = (
        "Waste collection schedule for the municipality of Baumkirchen, Austria."
    )
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "TestSource": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "menuonr": "218617457",
        },
    )
    parse = RiSKommunalParser()

    # Restmüll auto-resolves via the shared vocabulary; Plastikmüll has no
    # canonical alias and is mapped explicitly to the equivalent RECYCLABLES
    # type (matching the legacy Icons.PLASTIC_PACKAGING classification).
    transform = ICSTransformer(
        type_value_map={
            "Plastikmüll": RECYCLABLES,
        },
    )
