"""MPGK Katowice (mpgk.com.pl).

Demonstrates: a static ICS *POST* (the one variant of the plain-vanilla ICS
shape in this batch that isn't a GET). ``HttpPostRetriever`` + ``IcsParser`` +
``ICSTransformer`` do all the work; this module only supplies the POST body
and the waste-type map (mapped from the full observed ICS summaries — the
legacy source truncated each summary to its first word purely to look up an
icon, which is unnecessary now that the canonical type carries its own icon).

The legacy ``ICON_MAP`` never covered the "Odpady B I O..." (organic) summary
(its icon-lookup key derivation happened to yield "B", not a mapped key), so
that collection previously showed no icon at all. Mapped to ``ORGANIC`` here
as the obviously-intended category — a fix, not a behaviour change that loses
data either way.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://www.mpgk.com.pl/mod/harmonogram/ics"


@final
class Source(BaseSource):
    TITLE = "MPGK Katowice"
    DESCRIPTION = "Source for MPGK Katowice."
    URL = "https://www.mpgk.com.pl/"
    COUNTRY = "pl"

    TEST_CASES: ClassVar[dict] = {
        "Warszawska 17": {"street": "Warszawska", "number": 17},
        "3 Maja 38": {"street": "3 Maja", "number": "38"},
    }

    PARAMS = (
        street("street"),
        house_number("number"),
    )

    retrieve = HttpPostRetriever(
        url=_API_URL,
        data=lambda street, number, **_: {"street": street, "number": number},
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Odpady komunalne": GENERAL_WASTE,
            "Odpady papier, makulatura zbierane w pojemnikach 120 l do 1100 l": PAPER,
            "Odpady szklane zbierane w pojemnikach 120 l do 1100 l": GLASS,
            "Odpady wielkogabarytowe dla zabudowy wielorodzinnej": BULKY_WASTE,
            "Odpady z tworzyw sztucznych i metalu zbierane w pojemnikach"
            " 120 l do 1100 l": RECYCLABLES,
            "Odpady B I O zbierane w pojemnikach": ORGANIC,
        }
    )

    def __init__(self, street: str, number: str | int):
        super().__init__(street=street, number=number)
