"""Gruppo Veritas, Italy.

Demonstrates: the coordinate table-parser path on a two-months-per-page PDF
calendar. Gruppo Veritas publishes a per-municipality calendar whose every page
shows two months side by side, with each day cell holding waste-type badge
codes and, occasionally, a "raccolta sospesa" (collection suspended) or
"posticipata al ..." (postponed to ...) note. ``PdfTableParser`` returns each
text run with its coordinates grouped into rows, and
``preprocessors.PdfCalendarColumns`` bins those runs into the calendar's own
shape: one column per month, each with its heading runs and its numbered day
cells. All this source adds is what the printing *means*: the month and year in
the heading, the badge codes, and the two note rules. ``ICSTransformer`` maps the
badge codes onto canonical WasteTypes.
"""

import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import integer, text_field
from waste_collection_schedule.parsers import PdfTableParser
from waste_collection_schedule.preprocessors import (
    Compose,
    Deduplicate,
    PdfCalendarColumns,
    PdfColumn,
    PdfDayCell,
    RecurrenceExpander,
    RowFilter,
    Schedule,
)
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
# The two-digit year suffix printed in each month heading ("26" -> 2026). Each
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
# Heading runs (month name, decorative "20", year suffix, "PORTA A PORTA") sit
# above the grid; the topmost day cell starts well below this baseline.
_HEADER_Y = 845.0


def _column_month(header: tuple[str, ...]) -> int | None:
    """Read the month named in a column's heading."""
    for word in header:
        month = _MONTHS.get(word.strip().upper())
        if month is not None:
            return month
    return None


def _column_year(header: tuple[str, ...], fallback: int) -> int:
    """Read the two-digit year suffix from a column's heading, else fall back."""
    for word in header:
        match = _YEAR_RE.match(word)
        if match:
            return 2000 + int(match.group(1))
    return fallback


def _cell_schedules(cell: PdfDayCell, month: int, year: int) -> Iterable[Schedule]:
    """Resolve one day cell's badge codes and note into single-date schedules."""
    codes = set(_CODES_RE.findall(cell.text))

    postpone = _POSTPONE_RE.search(cell.text)
    if postpone:
        target_day = int(postpone.group(1))
        raw_month = postpone.group(2)
        target_month = int(raw_month) if raw_month else month
        target_year = year + 1 if raw_month and target_month < month else year
        try:
            date = datetime.date(target_year, target_month, target_day)
        except ValueError:
            return
    elif _SUSPEND_RE.search(cell.text):
        return
    else:
        try:
            date = datetime.date(year, month, cell.day)
        except ValueError:
            return

    for code in codes:
        yield Schedule(code, date)


def _describe(column: PdfColumn, source) -> Iterable[Schedule]:
    """Turn one month column into a single-date schedule per badge printed."""
    month = _column_month(column.header)
    if month is None:
        return
    year = _column_year(column.header, int(source.params["year"]))
    for cell in column.cells:
        yield from _cell_schedules(cell, month, year)


def _requested_year(row: tuple[datetime.date, str], source) -> bool:
    """Keep only the year the user asked for.

    Drops a postponement pushed into the next year, and any trailing next-year
    preview page the calendar carries.
    """
    return row[0].year == int(source.params["year"])


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

    preprocess = Compose(
        PdfCalendarColumns(
            column_bounds=(_COL_SPLIT,),
            day_bands=_DAY_BAND,
            header_y=_HEADER_Y,
        ),
        RecurrenceExpander(_describe),
        RowFilter(_requested_year),
        Deduplicate(),
    )

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
