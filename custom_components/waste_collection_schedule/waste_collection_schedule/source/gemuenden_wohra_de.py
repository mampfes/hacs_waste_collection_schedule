"""Stadt Gemünden (Wohra), Germany.

Demonstrates: a PDF month grid whose cells print codes rather than names. The
annual calendar PDF is linked (under a rotating hashed URL) from a stable page,
so ``PdfLinkRetriever`` finds it; the PDF is a twelve-month grid, so
``PdfTableParser`` returns its positioned runs and ``PdfMonthColumns`` finds the
months from the header row and reads the day cells. All this source supplies is
what a cell's printing means: the ``<code> <tour>`` tokens, filtered by the
resident's collection tour (``1/2`` means both), and the tour-independent tyre
(AR) and hazardous (SO) rounds.
"""

import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import integer
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import PdfTableParser
from waste_collection_schedule.preprocessors import PdfMonthColumns
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_SCHEDULE_URL = (
    "https://www.gemuenden-wohra.de/seite/461536/abfallentsorgung-abfuhrtermine.html"
)

# A day cell, e.g. "01 Do" (optionally followed by a holiday name).
_DAY_PATTERN = r"(\d{1,2})\s+(?:mo|di|mi|do|fr|sa|so)"
# A collection token: waste code + tour digit ("B 1", "P 2", "G 1/2").
_CODE_RE = re.compile(r"([BRGP])\s+(1/2|[12])")
_AR_RE = re.compile(r"\bAR\b")  # Altreifensammlung (waste tyres), tour-independent
_SO_RE = re.compile(r"\bSO\b")  # Sonderabfall (hazardous), tour-independent
_YEAR_PATTERN = r"\(Wohra\)\s*(\d{4})"

# The single-letter grid codes, spelled out as the labels the transform maps.
_CODE_LABELS = {
    "B": "Bioabfall",
    "R": "Restmüll",
    "G": "Gelbe Tonne",
    "P": "Altpapier",
}


def _read_cell(chunk: str, source) -> Iterable[str]:
    """The rounds a dated cell means, for this resident's collection tour."""
    tour = source.params["tour"] if source is not None else None
    for code, tour_digit in _CODE_RE.findall(chunk):
        if tour_digit == "1/2" or int(tour_digit) == tour:
            yield _CODE_LABELS[code]
    if _AR_RE.search(chunk):
        yield "Altreifensammlung"
    if _SO_RE.search(chunk):
        yield "Sonderabfall"


@final
class Source(BaseSource):
    TITLE = "Stadt Gemünden (Wohra)"
    DESCRIPTION = "Source for Stadt Gemünden (Wohra) waste collection schedule."
    URL = "https://www.gemuenden-wohra.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Tour 1 (Schiffelbach, Ellnrode, Grüsen etc.)": {"tour": 1},
        "Tour 2 (Kernstadt Gemünden)": {"tour": 2},
    }

    PARAMS = (integer("tour"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Tour 1: Schiffelbach, Ellnrode, Grüsen, Sehlen, Herbelhausen, "
            "Lehnhausen and areas west of the former railway line. "
            "Tour 2: rest of the Gemünden town centre."
        ),
        "de": (
            "Tour 1: Schiffelbach, Ellnrode, Grüsen, Sehlen, Herbelhausen, "
            "Lehnhausen und alle Grundstücke westlich der ehemaligen Bahntrasse. "
            "Tour 2: Rest der Kernstadt Gemünden."
        ),
    }

    retrieve = PdfLinkRetriever(
        index_url=_SCHEDULE_URL, pattern=r"Abfallkalender[_-]?(\d{4})\.pdf"
    )
    parse = PdfTableParser(min_words=20)
    preprocess = PdfMonthColumns(
        read_cell=_read_cell,
        day_pattern=_DAY_PATTERN,
        year_pattern=_YEAR_PATTERN,
    )

    transform = ICSTransformer(
        type_value_map={
            "Bioabfall": ORGANIC,
            "Restmüll": GENERAL_WASTE,
            "Altpapier": PAPER,
            "Gelbe Tonne": RECYCLABLES,
            "Sonderabfall": HAZARDOUS,
        }
    )

    def __init__(self, tour: int) -> None:
        if tour not in (1, 2):
            raise SourceArgumentNotFoundWithSuggestions("tour", str(tour), ["1", "2"])
        super().__init__(tour=tour)
