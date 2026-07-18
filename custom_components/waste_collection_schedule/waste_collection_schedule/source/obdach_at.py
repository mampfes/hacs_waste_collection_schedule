from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

_BASE_URL = "https://www.obdach.gv.at"


@final
class Source(BaseSource):
    TITLE = "Marktgemeinde Obdach"
    DESCRIPTION = "Source for Marktgemeinde Obdach, AT"
    URL = "https://www.obdach.gv.at/"
    COUNTRY = "at"

    TEST_CASES: ClassVar[dict] = {
        "TestSource": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalRetriever(base_url=_BASE_URL)
    parse = RiSKommunalParser()

    # Biomüll auto-resolves via the shared vocabulary. "Gelber Sack/Tonne"
    # combines both recyclables-bin names in one label and misses the
    # separate "gelber sack"/"gelbe tonne" aliases, so it needs an explicit
    # entry; the Restmüll labels carry a collection-area suffix.
    # "Altstoffsammelzentrum" (the recycling depot) is a drop-off centre, not
    # a kerbside round, and has no canonical equivalent, so it is left
    # unmapped and preserved verbatim, matching the legacy source (its
    # Icons.NEWSPAPER classification did not correspond to any of the
    # RECYCLABLES/PAPER meanings either).
    transform = ICSTransformer(
        type_value_map={
            "Gelber Sack/Tonne": RECYCLABLES,
            "Restmüll Abfuhrbereich 1": GENERAL_WASTE,
            "Restmüll Abfuhrbereich 2": GENERAL_WASTE,
        },
    )
