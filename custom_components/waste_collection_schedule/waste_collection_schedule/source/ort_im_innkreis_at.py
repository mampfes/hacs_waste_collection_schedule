from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE

_BASE_URL = "https://www.ort-im-innkreis.at"


@final
class Source(BaseSource):
    TITLE = "Ort im Innkreis"
    DESCRIPTION = "Waste collection schedule for Ort im Innkreis, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Default": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalRetriever(base_url=_BASE_URL)
    parse = RiSKommunalParser()

    # Only the frequency-suffixed residual-waste labels need an explicit
    # entry; every other label (Bioabfall, Altpapier, Gelber Sack, Altglas,
    # Sperrmüll, Problemstoff) is classified by the shared vocabulary.
    transform = ICSTransformer(
        type_value_map={
            "Restabfall 2-wöchentlich": GENERAL_WASTE,
            "Restabfall 4-wöchentlich": GENERAL_WASTE,
        },
    )
