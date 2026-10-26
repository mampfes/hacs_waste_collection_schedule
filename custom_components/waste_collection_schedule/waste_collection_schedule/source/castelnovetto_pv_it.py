"""Castelnovetto and neighbouring comuni (Lomellina, Pavia), Italy.

Impresa Sangalli collects door to door in Candia Lomellina, Castello
d'Agogna, Castelnovetto, Rosasco, Sant'Angelo Lomellina and Zeme on one shared
calendar. Castelnovetto publishes it every December as a news item ("Calendario
<year> raccolta rifiuti differenziata") on its Halley portal, the PDF behind a
script call that ``service.HalleyPortal`` follows.

The PDF prints two sheets of six month columns; only the round labels (UMIDO,
CARTA, ...) are text, the day numbers and month names being outlines, so
``service.PdfOutlinedCalendar.OutlinedDayRowsParser`` dates the labels by
position.
"""

from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.regions import region
from waste_collection_schedule.service import HalleyPortal
from waste_collection_schedule.service.PdfOutlinedCalendar import (
    OutlinedDayRowsParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.comune.castelnovetto.pv.it"
_NEWS_URL = f"{_URL}/novita/avvisi/avvisi.html"

_TYPES = {
    "UMIDO": wt.ORGANIC,
    "CARTA": wt.PAPER,
    "SECCO": wt.GENERAL_WASTE,
    "PLASTICA": wt.PLASTIC,
    "VETRO": wt.GLASS,
    "VERDE": wt.GARDEN_WASTE,
}

_COMUNI = (
    "Candia Lomellina",
    "Castello d'Agogna",
    "Castelnovetto",
    "Rosasco",
    "Sant'Angelo Lomellina",
    "Zeme",
)


@final
class Source(BaseSource):
    TITLE = "Castelnovetto, Candia Lomellina, Castello d'Agogna, Rosasco, Sant'Angelo Lomellina, Zeme"
    DESCRIPTION = (
        "Source for the shared door-to-door collection calendar of "
        "Castelnovetto and five neighbouring comuni (Lomellina, Pavia)."
    )
    URL = _URL
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.PAPER,
        wt.PLASTIC,
    ]

    TEST_CASES: ClassVar[dict] = {"Castelnovetto": {}}

    REGIONS = tuple(region(name) for name in _COMUNI)

    PARAMS = ()

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "No configuration is needed: Candia Lomellina, Castello d'Agogna, "
            "Castelnovetto, Rosasco, Sant'Angelo Lomellina and Zeme share one "
            "calendar, read from the yearly notice on Castelnovetto's website."
        ),
        "it": (
            "Nessuna configurazione necessaria: Candia Lomellina, Castello "
            "d'Agogna, Castelnovetto, Rosasco, Sant'Angelo Lomellina e Zeme "
            "condividono lo stesso calendario, letto dall'avviso annuale sul "
            "sito del Comune di Castelnovetto."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _NEWS_URL,
                pick=HalleyPortal.news_pick(r"calendario.*raccolta.*rifiuti"),
            ),
            retrievers.Lookup(
                lambda news, **_: news,
                pick=HalleyPortal.attachment_pick(r"calendario.*\.pdf"),
            ),
            HalleyPortal.download_lookup(),
        ),
        url=lambda _news, _attachment, path, **_: path,
    )
    parse = OutlinedDayRowsParser(
        _TYPES, year_pattern=r"(?:GIUGNO|DICEMBRE)\s+(20\d\d)"
    )
    transform = ICSTransformer(type_value_map=_TYPES)
