from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GARDEN_WASTE, GENERAL_WASTE, PAPER

_BASE_URL = "https://www.angern.at"


@final
class Source(BaseSource):
    TITLE = "Marktgemeinde Angern an der March"
    DESCRIPTION = "Source for Marktgemeinde Angern an der March, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "TestSource": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalRetriever(base_url=_BASE_URL)
    parse = RiSKommunalParser()

    # The calendar has no menuonr filter, so it also carries non-waste
    # municipal news items (Weingut/Buschenschank/Heurigen/Winzerwochen wine
    # events) which never matched the legacy ICON_MAP either; they are left
    # unmapped and preserved verbatim, as is "Recyclinghof" (a recycling
    # depot opening day, not a kerbside collection, so it does not equate to
    # the shared RECYCLABLES type) and "Bauschutt und Grünschnitt Stillfried"
    # (a combined rubble/green-waste day with no single canonical match).
    # Biotonne and Gelber Sack are classified by the shared vocabulary; the
    # location-suffixed Restmülltonne/Altpapiertonne/Grünschnitt labels need
    # explicit entries because the suffix breaks the exact-match resolution.
    transform = ICSTransformer(
        type_value_map={
            "Grünschnitt Ollersdorf": GARDEN_WASTE,
            "Grünschnitt Angern, Mannersdorf": GARDEN_WASTE,
            "Restmülltonne Angern": GENERAL_WASTE,
            "Restmülltonne Mannersdorf, Stillfried": GENERAL_WASTE,
            "Restmülltonne Grub, Ollersdorf": GENERAL_WASTE,
            "Altpapiertonne Angern": PAPER,
            "Altpapiertonne Mannersdorf, Stillfried": PAPER,
            "Altpapiertonne Grub, Ollersdorf": PAPER,
        },
    )
