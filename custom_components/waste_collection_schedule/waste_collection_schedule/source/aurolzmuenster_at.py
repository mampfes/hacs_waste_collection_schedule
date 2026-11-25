from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.aurolzmuenster.at"


@final
class Source(BaseSource):
    TITLE = "Aurolzmünster"
    DESCRIPTION = "Waste collection schedule for Aurolzmünster, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    # Bioabfall is published in two rhythms (bi-weekly / 4-weekly) that share
    # dates; both map to ORGANIC, so keep the raw label and suggest dedup.
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Default": {},
    }

    PARAMS = ()

    # The municipality's RiSKommunal calendar lists only the waste rounds of
    # the Bezirksabfallverband Ried (one round per waste type for the whole
    # municipality; Bioabfall is published in two rhythms).
    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "menuonr": "220039914",
        },
    )
    parse = RiSKommunalParser()

    transform = ICSTransformer(
        type_value_map={
            "Bioabfall 1/2 wöchentlich": wt.ORGANIC,
            "Bioabfall Biotonne 4 wöchentl.": wt.ORGANIC,
        },
        carry_raw_label=True,
    )
