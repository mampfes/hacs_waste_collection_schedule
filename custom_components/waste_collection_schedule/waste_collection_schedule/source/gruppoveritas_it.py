"""Gruppo Veritas, Italy.

Demonstrates: the coordinate table-parser path on a two-months-per-page PDF
calendar. Gruppo Veritas publishes a per-municipality calendar whose every page
shows two months side by side, with each day cell holding waste-type badge
codes and, occasionally, a "raccolta sospesa" (collection suspended) or
"posticipata al ..." (postponed to ...) note. ``PdfTableParser`` returns each
text run with its coordinates grouped into rows; this source splits every row
into a left and a right month column by ``x0``, bins the codes and notes of each
column into day cells by vertical position, and applies the suspension /
postponement rules. ``ICSTransformer`` maps the badge codes onto canonical
WasteTypes. The provider-specific part is only the column split, the day banding
and the two note rules; the coordinate extraction is the shared component's job.
"""

import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import integer, text_field
from waste_collection_schedule.parsers import PdfRow, PdfTableParser
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
)

DEFAULT_PDF_URL = (
    "https://www.gruppoveritas.it/sites/default/files/documenti/calendari/"
    "jesolo_calendario_raccolta_differenziata_2026.pdf"
)

_MONTHS = {
    "GENNAIO": 1,
    "FEBBRAIO": 2,
    "MARZO": 3,
    "APRILE": 4,
    "MAGGIO": 5,
    "GIUGNO": 6,
    "LUGLIO": 7,
    "AGOSTO": 8,
    "SETTEMBRE": 9,
    "OTTOBRE": 10,
    "NOVEMBRE": 11,
    "DICEMBRE": 12,
}

# Waste-type badge codes printed in each day cell (see the calendar legend):
#   C = Carta/Cartone, VPL = Vetro/Plastica/Lattine, S = Secco,
#   UO = Umido/Organico, VR = Verde/Ramaglie.
_CODES_RE = re.compile(r"\b(VPL|UO|VR|S|C)\b")
# "RACCOLTA SOSPESA" (collection suspended): drop the day entirely.
_SUSPEND_RE = re.compile(r"\bSOSPESA\b", re.IGNORECASE)
# "POSTICIPATA AL 5" / "POSTICIPATA AL 4/01" (postponed): re-emit the day's
# codes on the postponed date instead. A month earlier than the current one
# means the following year (a December collection pushed into January).
_POSTPONE_RE = re.compile(
    r"\bPOSTICIPATA\s+AL\s+(\d{1,2})(?:/(\d{1,2}))?\b", re.IGNORECASE
)
# The two-digit year suffix printed in each month header ("26" -> 2026). Each
# page carries its own, so a trailing next-year preview (dated e.g. "27") is
# detected here and dropped by the final year filter, exactly as the legacy
# source did.
_YEAR_RE = re.compile(r"^\s*(2[5-9])(\D|$)")

# Each page holds two months side by side; runs left of this x split belong to
# the first month, runs right of it to the second.
_COL_SPLIT = 300.0
# The x0 band the day-number run sits in, per column (the weekday abbreviation
# and the badge codes sit further right and so are excluded as day anchors).
_DAY_BAND = {0: (30.0, 66.0), 1: (340.0, 375.0)}
# Header runs (month name, decorative "20", year suffix, "PORTA A PORTA") sit
# above the grid; the topmost day cell starts well below this baseline.
_HEADER_Y = 845.0


@final
class Source(BaseSource):
    TITLE = "Gruppo Veritas"
    DESCRIPTION = (
        "Waste collection schedules published as PDF calendars by Gruppo "
        "Veritas (Jesolo and other municipalities)."
    )
    URL = "https://www.gruppoveritas.it/"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Jesolo_2026": {
            "pdf_url": DEFAULT_PDF_URL,
            "year": 2026,
        },
    }

    PARAMS = (
        text_field("pdf_url", "PDF Calendar URL", default=DEFAULT_PDF_URL),
        integer("year", "Year", default=2026),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://www.gruppoveritas.it, navigate to your municipality's "
            "waste collection page, locate the PDF calendar download link, and "
            "paste its URL into the pdf_url field."
        ),
        "it": (
            "Apri https://www.gruppoveritas.it, vai alla pagina del tuo Comune, "
            "trova il link al calendario PDF e incolla l'URL nel campo pdf_url."
        ),
    }

    retrieve = HttpGetRetriever(url=lambda pdf_url, **_: pdf_url)
    parse = PdfTableParser(min_words=200)

    # VPL is Vetro/Plastica/Lattine (glass, plastic and cans together); it is
    # mapped to GLASS to match the legacy icon intent, even though it also
    # covers plastic and metal packaging.
    transform = ICSTransformer(
        type_value_map={
            "S": GENERAL_WASTE,
            "UO": ORGANIC,
            "VR": GARDEN_WASTE,
            "C": PAPER,
            "VPL": GLASS,
        }
    )

    def __init__(self, pdf_url: str = DEFAULT_PDF_URL, year: int = 2026) -> None:
        super().__init__(pdf_url=pdf_url, year=year)

    def preprocess(
        self, rows: list[PdfRow], source=None
    ) -> Iterable[tuple[datetime.date, str]]:
        """Split each page into two month columns and yield (date, code) records.

        Deduplicates and keeps only the requested year, so a postponement pushed
        into the next year and any trailing next-year preview pages fall away.
        """
        param_year = int(self.params["year"])
        seen: set[tuple[datetime.date, str]] = set()
        for page in sorted({r.page for r in rows}):
            page_rows = [r for r in rows if r.page == page]
            for column, month in _month_columns(page_rows).items():
                year = _column_year(page_rows, column, param_year)
                for date, code in _parse_column(page_rows, column, month, year):
                    if date.year == param_year and (date, code) not in seen:
                        seen.add((date, code))
                        yield date, code


def _column_of(x0: float) -> int:
    return 0 if x0 < _COL_SPLIT else 1


def _month_columns(page_rows: list[PdfRow]) -> dict[int, int]:
    """Map each column index to the month named in that column's header."""
    columns: dict[int, int] = {}
    for row in page_rows:
        for word in row.words:
            month = _MONTHS.get(word.text.strip().upper())
            if month is not None:
                columns.setdefault(_column_of(word.x0), month)
    return columns


def _column_year(page_rows: list[PdfRow], column: int, fallback: int) -> int:
    """Read the two-digit year suffix from a column's header, else fall back."""
    for row in page_rows:
        if row.y <= _HEADER_Y:
            continue
        for word in row.words:
            if _column_of(word.x0) != column:
                continue
            match = _YEAR_RE.match(word.text)
            if match:
                return 2000 + int(match.group(1))
    return fallback


def _parse_column(
    page_rows: list[PdfRow], column: int, month: int, year: int
) -> list[tuple[datetime.date, str]]:
    """Bin one month column into day cells and resolve each cell's codes."""
    low, high = _DAY_BAND[column]
    anchors: list[tuple[float, int]] = []  # (y, day number)
    notes: list[tuple[float, str]] = []  # (y, text) of every other run
    for row in page_rows:
        if row.y >= _HEADER_Y:
            continue
        for word in row.words:
            if _column_of(word.x0) != column:
                continue
            if (
                low <= word.x0 <= high
                and word.text.isdigit()
                and 1 <= int(word.text) <= 31
            ):
                anchors.append((row.y, int(word.text)))
            else:
                notes.append((row.y, word.text))

    if not anchors:
        return []
    anchors.sort(key=lambda a: -a[0])

    # Assign each note run to the day whose anchor is vertically nearest.
    cells: dict[int, list[tuple[float, str]]] = {i: [] for i in range(len(anchors))}
    for note_y, text in notes:
        nearest = min(range(len(anchors)), key=lambda i: abs(anchors[i][0] - note_y))
        cells[nearest].append((note_y, text))

    events: list[tuple[datetime.date, str]] = []
    for index, (_, day_num) in enumerate(anchors):
        combined = " ".join(
            text for _, text in sorted(cells[index], key=lambda p: -p[0])
        )
        codes = set(_CODES_RE.findall(combined))

        postpone = _POSTPONE_RE.search(combined)
        if postpone:
            target_day = int(postpone.group(1))
            raw_month = postpone.group(2)
            target_month = int(raw_month) if raw_month else month
            target_year = year + 1 if raw_month and target_month < month else year
            try:
                date = datetime.date(target_year, target_month, target_day)
            except ValueError:
                continue
            events.extend((date, code) for code in codes)
            continue

        if _SUSPEND_RE.search(combined):
            continue

        try:
            date = datetime.date(year, month, day_num)
        except ValueError:
            continue
        events.extend((date, code) for code in codes)
    return events
