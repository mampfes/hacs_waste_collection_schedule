"""Stadt Ansbach, Germany.

The city publishes one PDF calendar per street (or district) through its
p-42.net download service. The file name is deterministic,
``Stadt Ansbach-<street>.pdf`` (Latin-1 encoded). The PDF is two pages of six
month columns each; a day cell such as ``02 Fr R`` carries the round codes
R (Restabfall), GS (Gelber Sack), P (Papierabfall) and B (Bioabfall), the
latter often printed as a separate run at the right edge of the cell, which is
why the columns are cut at fixed positions (``PdfCalendarColumns``) rather than
at month-heading midpoints.
"""

import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final
from urllib.parse import quote

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.parsers import ArgumentGuard, PdfTableParser
from waste_collection_schedule.preprocessors import (
    Compose,
    Deduplicate,
    PdfCalendarColumns,
    PdfColumn,
    PdfDayCell,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

_DOWNLOAD_URL = "https://www.p-42.net/cal/sansb2/download.php?file="

# Each half-year page prints six month columns side by side, 132 pt apart.
# A day cell is one run "<day> <weekday> [holiday] [codes]"; codes printed
# further right in the cell are separate runs on the same line.
_COLUMN_PITCH = 132.06
_FIRST_DAY_X = 41.5
_COLUMN_BOUNDS = tuple(_FIRST_DAY_X - 10 + _COLUMN_PITCH * i for i in range(1, 6))
_DAY_BANDS = {
    i: (_FIRST_DAY_X + _COLUMN_PITCH * i - 6, _FIRST_DAY_X + _COLUMN_PITCH * i + 6)
    for i in range(6)
}
_HEADER_Y = 497.0  # below the month-name and "KW" heading rows
_DAY_PATTERN = r"(\d{1,2})\b"

_CODE_RE = re.compile(r"\b(GS|R|P|B)\b")
_CODE_LABELS = {
    "R": "Restabfall",
    "GS": "Gelber Sack",
    "P": "Papierabfall",
    "B": "Bioabfall",
}


def _column_year(month: int, cells: "tuple[PdfDayCell, ...]") -> "int | None":
    """The year whose calendar matches the printed weekday of the 1st."""
    first = next((cell for cell in cells if cell.day == 1), None)
    if first is None or not first.text:
        return None
    printed = recurrence.weekday(first.text.split()[0], "de", abbreviated=True)
    if printed is None:
        return None
    this_year = datetime.date.today().year
    for year in (this_year, this_year + 1, this_year - 1):
        if datetime.date(year, month, 1).weekday() == printed:
            return year
    return None


def _describe(column: PdfColumn, source: "BaseSource | None") -> Iterable[Schedule]:
    """One month column (Jan-Jun on page 1, Jul-Dec on page 2) to schedules."""
    month = column.page * 6 + column.column + 1
    if not 1 <= month <= 12:
        return
    year = _column_year(month, column.cells)
    if year is None:
        return
    for cell in column.cells:
        # Drop the weekday so a holiday name never reads as a code.
        body = cell.text.split(maxsplit=1)[1] if " " in cell.text else ""
        try:
            date = datetime.date(year, month, cell.day)
        except ValueError:
            continue
        for code in dict.fromkeys(_CODE_RE.findall(body)):
            yield Schedule(_CODE_LABELS[code], date)


def _pdf_url(street: str, **_: object) -> str:
    filename = f"Stadt Ansbach-{street.strip()}.pdf"
    return _DOWNLOAD_URL + quote(filename.encode("latin-1", errors="replace"))


@final
class Source(BaseSource):
    TITLE = "Stadt Ansbach"
    DESCRIPTION = "Source for Stadt Ansbach (city), Germany."
    URL = "https://www.ansbach.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Feuchtwanger Straße": {"street": "Feuchtwanger Straße"},
        "Schalkhausen": {"street": "Schalkhausen"},
    }

    PARAMS = (street(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street exactly as listed on "
            "https://www.ansbach.de/B%C3%BCrger/Umwelt-Natur/Abfall-Recycling/Abfuhrpl%C3%A4ne "
            "(e.g. 'Feuchtwanger Straße'). For the districts Bernhardswinden, "
            "Brodswinden, Claffheim, Elpersdorf, Höfstetten, Kaltengreuth, "
            "Meinhardswinden, Neuses, Obereichenbach and Schalkhausen enter the "
            "district name instead."
        ),
        "de": (
            "Straße genau wie in der Auswahl auf "
            "https://www.ansbach.de/B%C3%BCrger/Umwelt-Natur/Abfall-Recycling/Abfuhrpl%C3%A4ne "
            "angeben (z. B. 'Feuchtwanger Straße'). Für die Stadtteile "
            "Bernhardswinden, Brodswinden, Claffheim, Elpersdorf, Höfstetten, "
            "Kaltengreuth, Meinhardswinden, Neuses, Obereichenbach und Schalkhausen "
            "den Stadtteilnamen angeben."
        ),
    }

    retrieve = HttpGetRetriever(url=_pdf_url)
    parse = ArgumentGuard(
        PdfTableParser(min_words=100),
        argument="street",
        matches=lambda response, _source: response.content.lstrip().startswith(
            b"%PDF-"
        ),
        hint="spell the street exactly as in the street list on the Ansbach "
        "Abfuhrpläne page",
    )
    preprocess = Compose(
        PdfCalendarColumns(
            column_bounds=_COLUMN_BOUNDS,
            day_bands=_DAY_BANDS,
            header_y=_HEADER_Y,
            day_pattern=_DAY_PATTERN,
        ),
        RecurrenceExpander(_describe),
        Deduplicate(),
    )
    transform = ICSTransformer(
        type_value_map={
            "Restabfall": wt.GENERAL_WASTE,
            "Gelber Sack": wt.RECYCLABLES,
            "Papierabfall": wt.PAPER,
            "Bioabfall": wt.ORGANIC,
        }
    )
