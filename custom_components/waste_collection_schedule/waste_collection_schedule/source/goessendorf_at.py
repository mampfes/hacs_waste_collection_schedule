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
    RAISE_ON_EMPTY = True

    # Derived by replaying the cassette, which this source could not do before:
    # it had none, so nothing had ever checked what it produces. The list is
    # wider than type_value_map suggests because Bioabfall, Leicht- und
    # Metallverpackungen and Strauchschnittsammlung resolve via the shared
    # vocabulary rather than being listed.
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestSource": {},
    }

    PARAMS = ()

    # Gössendorf's calendar defaults to a single day, so requesting it with no
    # parameters returned a page with no entries and the source reported no
    # collections at all, reproducibly. ``bdatum`` opens the window to the
    # whole published schedule. This install also renders as a paginated list
    # rather than a table, so the parser must keep paging: stopping after page
    # one would read six weeks of a five-month schedule.
    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={"bdatum": "31.12.9999", "menuonr": "224962693"},
    )
    parse = RiSKommunalParser(paginate_list=True)

    # Bioabfall auto-resolves via the shared vocabulary. Every other label
    # carries a collection-area suffix (P1/P2, S1/S2, R1/R2) that breaks
    # exact-match resolution against the base Altpapier/Sperrmüll/Restmüll
    # aliases, so each needs an explicit entry. "Gefäßreinigung Bioabfall" is
    # the organic bin's wash, which rides along with a round rather than being
    # one, so it is dropped rather than left as an unresolved label.
    transform = ICSTransformer(
        type_value_map={
            "Altpapier P1": wt.PAPER,
            "Altpapier P2": wt.PAPER,
            "Sperrmüll S1": wt.BULKY_WASTE,
            "Sperrmüll S2": wt.BULKY_WASTE,
            "Restmüll R1": wt.GENERAL_WASTE,
            "Restmüll R2": wt.GENERAL_WASTE,
            "Gefäßreinigung Bioabfall": None,
        },
    )
