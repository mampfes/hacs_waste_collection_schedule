from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

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

    # The vocabulary this feed actually produces, derived by replaying the
    # recorded cassette. Declared explicitly because most of these labels are
    # resolved by the shared vocabulary rather than listed in type_value_map,
    # so the auto-derived set would be incomplete.
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

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
            "Plastikmüll": wt.RECYCLABLES,
        },
    )
