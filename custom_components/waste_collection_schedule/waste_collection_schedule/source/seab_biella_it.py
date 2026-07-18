"""SEAB Biella, Italy.

Demonstrates: the coordinate table-parser path. SEAB publishes a per-municipality
calendar PDF showing six months side-by-side, which plain text extraction
collapses. ``PdfTableParser`` returns each text run with its coordinates grouped
into rows; this source detects the month columns from the header row's x-
positions, bins each row's runs into those columns, and reads the day number and
waste keyword from each cell. ``ICSTransformer`` maps the Italian labels onto
canonical WasteTypes. The per-provider part is only "which x range is which
month"; the fiddly coordinate extraction is the shared component's job.
"""

import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.parsers import PdfRow, PdfTableParser
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
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
_WASTE_LABELS = ("INDIFFERENZIATO", "ORGANICO", "CARTA", "PLASTICA", "VETRO", "SFALCI")

# A day cell within a column, e.g. "01 gio" / "15 mer".
_DAY_RE = re.compile(r"(\d{1,2})\s+[a-z]{3}")
_YEAR_RE = re.compile(r"Raccolta rifiuti (\d{4})")


def _month_columns(page_rows: list[PdfRow]) -> "list[tuple[float, int]] | None":
    """Detect (x0, month) per column from the header row that names the months."""
    for row in page_rows:
        found = [
            (w.x0, _MONTHS[w.text.upper()])
            for w in row.words
            if w.text.upper() in _MONTHS
        ]
        if len(found) >= 2:
            return sorted(found)
    return None


@final
class Source(BaseSource):
    TITLE = "SEAB Biella"
    DESCRIPTION = "Source for SEAB Biella (Italy) waste collection."
    URL = "https://www.seab.biella.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Ailoche": {
            "url": "https://www.seab.biella.it/wp-content/uploads/2026/05/Ailoche-II-semestre.pdf"
        },
        "Andorno Micca": {
            "url": "https://www.seab.biella.it/wp-content/uploads/2026/05/Andorno-Micca-II-semestre.pdf"
        },
    }

    PARAMS = (text_field("url", "Calendar PDF URL"),)

    HOWTO: ClassVar[dict] = {
        "it": (
            "Visita https://www.seab.biella.it/aree-servite, seleziona il tuo "
            "comune e copia il link al file PDF del calendario."
        ),
        "en": (
            "Visit https://www.seab.biella.it/aree-servite, select your "
            "municipality and copy the link to the PDF calendar file."
        ),
    }

    retrieve = HttpGetRetriever(url=lambda url: url)
    parse = PdfTableParser(min_words=50)

    transform = ICSTransformer(
        type_value_map={
            "INDIFFERENZIATO": GENERAL_WASTE,
            "ORGANICO": ORGANIC,
            "CARTA": PAPER,
            "PLASTICA": RECYCLABLES,
            "VETRO": GLASS,
            "SFALCI": GARDEN_WASTE,
        }
    )

    def __init__(self, url: str) -> None:
        super().__init__(url=url)

    def preprocess(
        self, rows: list[PdfRow], source=None
    ) -> Iterable[tuple[datetime.date, str]]:
        """Bin each row into month columns; yield (date, label) per waste cell."""
        year_match = _YEAR_RE.search(" ".join(w.text for r in rows for w in r.words))
        year = int(year_match.group(1)) if year_match else datetime.date.today().year

        for page in sorted({r.page for r in rows}):
            page_rows = [r for r in rows if r.page == page]
            columns = _month_columns(page_rows)
            if not columns:
                continue
            xs = [x for x, _ in columns]
            months = [m for _, m in columns]
            # Column boundaries are the midpoints between adjacent month headers.
            mids = [(xs[i] + xs[i + 1]) / 2 for i in range(len(xs) - 1)]

            def column_of(x: float, mids: list[float] = mids) -> int:
                return sum(1 for mid in mids if x >= mid)

            for row in page_rows:
                cells: dict[int, list[str]] = {}
                for word in row.words:
                    cells.setdefault(column_of(word.x0), []).append(word.text)
                for col, texts in cells.items():
                    chunk = " ".join(texts).upper()
                    day_match = _DAY_RE.search(chunk.lower())
                    if not day_match:
                        continue
                    try:
                        collection_date = datetime.date(
                            year, months[col], int(day_match.group(1))
                        )
                    except ValueError:
                        continue
                    for label in _WASTE_LABELS:
                        if label in chunk:
                            yield collection_date, label
