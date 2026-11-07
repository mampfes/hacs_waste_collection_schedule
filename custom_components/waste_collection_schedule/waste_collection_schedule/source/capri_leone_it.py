"""Door-to-door waste collections for Capri Leone (Messina), Italy.

The municipality publishes dated collections through the public Comune Smart
(Internavigare) API. Its municipality access token is an app identifier, not a
personal Home Assistant credential.
"""

from typing import ClassVar, TypedDict, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

_EVENTS_URL = "https://comuni.internavigare.com/backend/api/v1/rifiuti-evento"
_MUNICIPALITY_TOKEN = "n-PRl8rIpm"


class _WasteEvent(TypedDict):
    data: str
    titolo: str


@final
class Source(BaseSource):
    TITLE = "Capri Leone"
    DESCRIPTION = "Door-to-door waste collection schedule for Capri Leone (ME), Italy."
    URL = "https://comune.caprileone.me.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {"Capri Leone": {}}
    PARAMS = ()
    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.PLASTIC,
        wt.PAPER,
        wt.GLASS,
        wt.METAL,
        wt.GENERAL_WASTE,
    ]

    HOWTO: ClassVar[dict[str, str]] = {
        "en": "No configuration needed: this source covers Capri Leone (ME).",
        "it": "Non sono richiesti parametri: la fonte copre Capri Leone (ME).",
    }

    retrieve = HttpGetRetriever(
        url=_EVENTS_URL,
        params=lambda **_: {"access-token": _MUNICIPALITY_TOKEN},
    )
    parse = parsers.JsonParser(shape=list[_WasteEvent])
    transform = JsonTransformer(
        date_key="data",
        type_key="titolo",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Ritiro Organico": wt.ORGANIC,
            "Ritiro Plastica": wt.PLASTIC,
            "Ritiro Carta e Cartone": wt.PAPER,
            "Ritiro Vetro e Lattine": [wt.GLASS, wt.METAL],
            "Ritiro Indifferenziato": wt.GENERAL_WASTE,
        },
    )
