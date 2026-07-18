"""Stadt Gemünden (Wohra), Germany.

Demonstrates: both new PDF components composed on one source. The annual
calendar PDF is linked (under a rotating hashed URL) from a stable page, so
``PdfLinkRetriever`` finds it; the PDF is a twelve-month grid, so
``PdfTableParser`` returns its positioned runs. This source detects the twelve
month columns from the header row and bins each row's runs into them, reading
the day cell and the ``<code> <tour>`` collection tokens from each cell. The
provider-specific part is the tour filter (a resident's collection tour selects
which tokens apply; ``1/2`` means both) and the tour-independent tyre (AR) and
hazardous (SO) rounds -- expressed here rather than in a generic transformer.
"""

import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import integer
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import PdfRow, PdfTableParser
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

_MONTHS = {
    "JANUAR": 1,
    "FEBRUAR": 2,
    "MÄRZ": 3,
    "APRIL": 4,
    "MAI": 5,
    "JUNI": 6,
    "JULI": 7,
    "AUGUST": 8,
    "SEPTEMBER": 9,
    "OKTOBER": 10,
    "NOVEMBER": 11,
    "DEZEMBER": 12,
}
# A day cell, e.g. "01 Do" (optionally followed by a holiday name).
_DAY_RE = re.compile(r"(\d{1,2})\s+(?:Mo|Di|Mi|Do|Fr|Sa|So)")
# A collection token: waste code + tour digit ("B 1", "P 2", "G 1/2").
_CODE_RE = re.compile(r"([BRGP])\s+(1/2|[12])")
_AR_RE = re.compile(r"\bAR\b")  # Altreifensammlung (waste tyres), tour-independent
_SO_RE = re.compile(r"\bSO\b")  # Sonderabfall (hazardous), tour-independent
_YEAR_RE = re.compile(r"\(Wohra\)\s*(\d{4})")

# The single-letter grid codes, spelled out as the labels the transform maps.
_CODE_LABELS = {
    "B": "Bioabfall",
    "R": "Restmüll",
    "G": "Gelbe Tonne",
    "P": "Altpapier",
}


def _month_columns(page_rows: list[PdfRow]) -> "tuple[list[float], list[int]] | None":
    """Detect the month header row; return its column x-positions and months."""
    for row in page_rows:
        found = sorted(
            (w.x0, _MONTHS[w.text.upper()])
            for w in row.words
            if w.text.upper() in _MONTHS
        )
        if len(found) >= 6:
            return [x for x, _ in found], [m for _, m in found]
    return None


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

    def preprocess(
        self, rows: list[PdfRow], source=None
    ) -> Iterable[tuple[datetime.date, str]]:
        """Bin the grid into month columns; yield (date, label) per collection."""
        tour = self.params["tour"]
        text = " ".join(w.text for r in rows for w in r.words)
        year_match = _YEAR_RE.search(text)
        year = int(year_match.group(1)) if year_match else datetime.date.today().year

        # The calendar grid is on the first page.
        page_rows = [r for r in rows if r.page == 0]
        columns = _month_columns(page_rows)
        if not columns:
            return
        xs, months = columns
        header_y = next(
            r.y
            for r in page_rows
            if sum(w.text.upper() in _MONTHS for w in r.words) >= 6
        )
        mids = [(xs[i] + xs[i + 1]) / 2 for i in range(len(xs) - 1)]

        def column_of(x: float) -> int:
            return sum(1 for mid in mids if x >= mid)

        for row in page_rows:
            # Rows above the header are the title and the Dec-preamble; skip them.
            if row.y >= header_y:
                continue
            cells: dict[int, list[str]] = {}
            for word in row.words:
                cells.setdefault(column_of(word.x0), []).append(word.text)
            for col, texts in cells.items():
                chunk = " ".join(texts)
                day_match = _DAY_RE.search(chunk)
                if not day_match:
                    continue
                try:
                    collection_date = datetime.date(
                        year, months[col], int(day_match.group(1))
                    )
                except ValueError:
                    continue
                for code, tour_digit in _CODE_RE.findall(chunk):
                    if tour_digit == "1/2" or int(tour_digit) == tour:
                        yield collection_date, _CODE_LABELS[code]
                if _AR_RE.search(chunk):
                    yield collection_date, "Altreifensammlung"
                if _SO_RE.search(chunk):
                    yield collection_date, "Sonderabfall"
