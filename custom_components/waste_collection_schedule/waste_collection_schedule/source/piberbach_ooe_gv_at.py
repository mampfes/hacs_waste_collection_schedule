from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE

_BASE_URL = "https://www.piberbach.ooe.gv.at"


@final
class Source(BaseSource):
    TITLE = "Piberbach"
    DESCRIPTION = "Source for Piberbach, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Piberbacherstraße 20": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
        },
    )
    parse = RiSKommunalParser()

    # Only the frequency-suffixed residual-waste labels need an explicit entry;
    # every other label (Bioabfall, Altpapier, Gelber Sack) is classified by
    # the shared vocabulary.
    transform = ICSTransformer(
        type_value_map={
            "Restabfall 2-wöchentlich": GENERAL_WASTE,
            "Restabfall 4-wöchentlich": GENERAL_WASTE,
            "Restabfall 6-wöchentlich": GENERAL_WASTE,
        },
    )
