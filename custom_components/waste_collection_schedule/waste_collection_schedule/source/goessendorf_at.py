from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.goessendorf.com"


@final
class Source(BaseSource):
    TITLE = "Marktgemeinde Gössendorf"
    DESCRIPTION = "Source for Marktgemeinde Gössendorf, AT"
    URL = "https://www.goessendorf.com/"
    COUNTRY = "at"

    TEST_CASES: ClassVar[dict] = {
        "TestSource": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalRetriever(base_url=_BASE_URL)
    parse = RiSKommunalParser()

    # Bioabfall auto-resolves via the shared vocabulary. Every other label
    # carries a collection-area suffix (P1/P2, S1/S2, R1/R2) that breaks
    # exact-match resolution against the base Altpapier/Sperrmüll/Restmüll
    # aliases, so each needs an explicit entry.
    transform = ICSTransformer(
        type_value_map={
            "Altpapier P1": wt.PAPER,
            "Altpapier P2": wt.PAPER,
            "Sperrmüll S1": wt.BULKY_WASTE,
            "Sperrmüll S2": wt.BULKY_WASTE,
            "Restmüll R1": wt.GENERAL_WASTE,
            "Restmüll R2": wt.GENERAL_WASTE,
        },
    )
