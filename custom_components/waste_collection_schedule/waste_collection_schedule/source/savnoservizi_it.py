"""Savno Servizi, Italy.

Savno publishes one yearly PDF calendar per comune (or zone of a comune) on
https://www.savnoservizi.it/it/avvisi-e-download/download/calendari. The
calendar has a page per month (from January into the next year) listing every
day ("2 VEN") with the rounds collected that day (UMIDO, SECCO, CARTA, ...)
printed beside it, apart from the day's text, so its rows are rebuilt from the
positioned words.
"""

import re
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import config_params, lookups, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.PdfTextCalendar import (
    DayGridCalendarParser,
    LabelRule,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.savnoservizi.it"
_INDEX_URL = f"{_URL}/it/avvisi-e-download/download/calendari"

_COMUNE = re.compile(r"per il comune di\s+(.+)$", re.IGNORECASE)

ORGANIC = "Umido"
RESIDUAL = "Secco"
PLASTIC = "Plastica e lattine"
PAPER = "Carta"
GLASS = "Vetro"
GARDEN = "Verde"


def _comune(link: Tag) -> str:
    """'Calendario Savno 2026 per il comune di Oderzo – zona 3' -> 'Oderzo – zona 3'."""
    match = _COMUNE.search(link.get_text(" ", strip=True))
    return match.group(1) if match else ""


@final
class Source(BaseSource):
    TITLE = "Savno Servizi"
    DESCRIPTION = "Source for Savno Servizi (Treviso, Veneto) collection calendars."
    URL = _URL
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Oderzo – zona 3": {"comune": "Oderzo – zona 3"},
        "Cessalto": {"comune": "Cessalto"},
        "Conegliano – zona Blu": {"comune": "Conegliano zona Blu"},
    }

    PARAMS = (config_params.municipality("comune"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your comune as listed on "
            "https://www.savnoservizi.it/it/avvisi-e-download/download/calendari "
            "after 'per il comune di', including the zone where there is one, "
            "for example `Oderzo – zona 3`."
        ),
        "it": (
            "Inserisci il tuo comune come indicato su "
            "https://www.savnoservizi.it/it/avvisi-e-download/download/calendari "
            "dopo 'per il comune di', con la zona se presente, ad esempio "
            "`Oderzo – zona 3`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL,
                pick=lookups.link_pick(
                    "comune", href=r"/download/\d+\?f=open$", label=_comune
                ),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=90,
    )
    parse = DayGridCalendarParser(
        labels=[
            LabelRule(ORGANIC, r"\bUMIDO\b"),
            LabelRule(RESIDUAL, r"\bSECCO\b"),
            LabelRule(PLASTIC, r"\bPLASTICA"),
            LabelRule(PAPER, r"\bCARTA\b"),
            LabelRule(GLASS, r"\bVETRO\b"),
            LabelRule(GARDEN, r"\bVERDE\b"),
        ],
        months_per_page=None,
        weekday_order=("LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"),
        line_pattern=r"^(\d{1,2})\s+([A-Za-z]{3})\b\s*(.*)",
        layout=True,
        # The year stands on a line of its own above January.
        year_text_pattern=r"(?m)^\s*(20\d{2})\s*$",
    )
    transform = ICSTransformer(
        type_value_map={
            ORGANIC: wt.ORGANIC,
            RESIDUAL: wt.GENERAL_WASTE,
            PLASTIC: wt.RECYCLABLES,
            PAPER: wt.PAPER,
            GLASS: wt.GLASS,
            GARDEN: wt.GARDEN_WASTE,
        }
    )
