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

    # Angern runs two calendars on one install, and asking for neither returns
    # both merged: the waste calendar (typids=224965250) and the wine taverns'
    # opening seasons (typids=224966905). That is how ten Heurigen,
    # Buschenschänke and Weingüter came to appear in Home Assistant as bin
    # collections. These ids are the ones the municipality's own Abfuhrtermine
    # page links to.
    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "detailonr": "224965250",
            "menuonr": "226137057",
            "typids": "224965250",
        },
    )
    parse = RiSKommunalParser()

    # Biotonne and Gelber Sack are classified by the shared vocabulary; the
    # location-suffixed Restmülltonne/Altpapiertonne/Grünschnitt labels need
    # explicit entries because the suffix breaks the exact-match resolution.
    #
    # Two entries are judgements rather than translations. "Bauschutt und
    # Grünschnitt Stillfried" is a dated container day at Stillfried taking
    # rubble and green cuttings: it is a collection, and Grünschnitt is the
    # half with a canonical home, so it joins Angern's other Grünschnitt
    # rounds as GARDEN_WASTE. "Recyclinghof" is the opposite case, the
    # recycling centre's ordinary opening days rather than a round, so mapping
    # its 14 entries to RECYCLABLES would raise a recycling reminder on days
    # when no bin goes out. It is dropped instead, which states that the label
    # is known and is not a collection rather than leaving it unresolved.
    transform = ICSTransformer(
        type_value_map={
            "Grünschnitt Ollersdorf": wt.GARDEN_WASTE,
            "Grünschnitt Angern, Mannersdorf": wt.GARDEN_WASTE,
            "Bauschutt und Grünschnitt Stillfried": wt.GARDEN_WASTE,
            "Recyclinghof": None,
            "Restmülltonne Angern": wt.GENERAL_WASTE,
            "Restmülltonne Mannersdorf, Stillfried": wt.GENERAL_WASTE,
            "Restmülltonne Grub, Ollersdorf": wt.GENERAL_WASTE,
            "Altpapiertonne Angern": wt.PAPER,
            "Altpapiertonne Mannersdorf, Stillfried": wt.PAPER,
            "Altpapiertonne Grub, Ollersdorf": wt.PAPER,
        },
    )
