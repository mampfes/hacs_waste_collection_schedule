from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.ort-im-innkreis.at"


@final
class Source(BaseSource):
    TITLE = "Ort im Innkreis"
    DESCRIPTION = "Waste collection schedule for Ort im Innkreis, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    # The vocabulary this feed actually produces, derived by replaying the
    # recorded cassette. Declared explicitly because most of these labels are
    # resolved by the shared vocabulary rather than listed in type_value_map,
    # so the auto-derived set would be incomplete.
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

    # Ort im Innkreis publishes only waste rounds on its calendar today, so the
    # unfiltered request was right by accident. Its Abfuhrtermine page selects
    # four waste calendars explicitly, which is what this now asks for, so a
    # municipal event added later cannot leak in.
    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "sprache": "1",
            "menuonr": "225603223",
            "typids": "227719961,227719962,227719963,227869194",
        },
    )
    parse = RiSKommunalParser()

    # Only the frequency-suffixed residual-waste labels need an explicit
    # entry; every other label (Bioabfall, Altpapier, Gelber Sack, Altglas,
    # Sperrmüll, Problemstoff) is classified by the shared vocabulary.
    transform = ICSTransformer(
        type_value_map={
            "Restabfall 2-wöchentlich": wt.GENERAL_WASTE,
            "Restabfall 4-wöchentlich": wt.GENERAL_WASTE,
        },
    )
