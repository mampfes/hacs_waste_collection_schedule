from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE

# Demonstrates: the RiSKommunal platform contributing TWO independent pipeline
# stages — RiSKommunalRetriever (raw HTML calendar pages, fetched lazily) and
# RiSKommunalParser (pages -> (date, label) rows) — kept strictly separate.
#
# The retriever owns the multi-request acquisition (pagination, and address ->
# typids resolution when configured); the parser owns extraction and the
# stop-when-done decision, pulling only as many pages as it needs. A plain
# ICSTransformer then maps each label onto a canonical WasteType. The source
# itself is fully declarative — no fetch(), retrieve() or parse() code.


class Source(BaseSource):
    TITLE = "Koppl"
    DESCRIPTION = "Waste collection schedule for Koppl, Austria."
    URL = "https://www.koppl.at"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Koppl": {},
    }

    PARAMS = []

    retrieve = RiSKommunalRetriever(
        base_url="https://www.koppl.at",
        query_params={
            "bdatum": "31.12.9999",
            "detailonr": "225241960",
            "menuonr": "225241969",
            "typids": "225241960",
        },
    )
    parse = RiSKommunalParser()

    # Only the frequency-suffixed residual-waste labels need an explicit entry;
    # every other label (Restmüll, Bioabfall, Altpapier, Gelber Sack, Altglas,
    # Sperrmüll, Problemstoff, ...) is classified by the shared vocabulary.
    transformer = ICSTransformer(
        type_value_map={
            "Restabfall 14-tägig": GENERAL_WASTE,
            "Restabfall monatlich": GENERAL_WASTE,
        },
    )
