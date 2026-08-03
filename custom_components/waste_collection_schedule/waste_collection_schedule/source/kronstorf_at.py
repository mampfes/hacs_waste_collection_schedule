from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.kronstorf.at"


@final
class Source(BaseSource):
    TITLE = "Kronstorf"
    DESCRIPTION = "Source for Kronstorf (Marktgemeinde Kronstorf), Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Kronstorf": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "menuonr": "218754346",
            "bdatum": "31.12.9999",
        },
    )
    parse = RiSKommunalParser()

    # Only the frequency-suffixed residual-waste labels need an explicit entry;
    # every other label (Restmüll, Bioabfall, Biomüll, Altpapier, Papier,
    # Gelber Sack, Gelbe Tonne, Sperrmüll, Altglas, Problemstoff) is classified
    # by the shared vocabulary.
    transform = ICSTransformer(
        type_value_map={
            "Restabfall wöchentlich": wt.GENERAL_WASTE,
            "Restabfall 2-wöchentlich": wt.GENERAL_WASTE,
            "Restabfall 4-wöchentlich": wt.GENERAL_WASTE,
            "Restabfall 6-wöchentlich": wt.GENERAL_WASTE,
        },
    )
