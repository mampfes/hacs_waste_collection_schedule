from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.angern.at"


@final
class Source(BaseSource):
    TITLE = "Marktgemeinde Angern an der March"
    DESCRIPTION = "Source for Marktgemeinde Angern an der March, Austria."
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
        wt.GARDEN_WASTE,
    ]

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
            "Grünschnitt Ollersdorf": wt.GARDEN_WASTE,
            "Grünschnitt Angern, Mannersdorf": wt.GARDEN_WASTE,
            "Restmülltonne Angern": wt.GENERAL_WASTE,
            "Restmülltonne Mannersdorf, Stillfried": wt.GENERAL_WASTE,
            "Restmülltonne Grub, Ollersdorf": wt.GENERAL_WASTE,
            "Altpapiertonne Angern": wt.PAPER,
            "Altpapiertonne Mannersdorf, Stillfried": wt.PAPER,
            "Altpapiertonne Grub, Ollersdorf": wt.PAPER,
        },
    )
