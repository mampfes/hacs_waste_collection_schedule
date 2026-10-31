"""Nemenčinės komunalininkas (nemenkom.lt) XLSX schedule retrieval and parsing."""

import datetime as dt
import re
from typing import Any

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser, XlsxParser

PAGE_URL = "https://www.nemenkom.lt/buitiniu-ir-pakuociu-atlieku-surinkimo-grafikas/"
MAX_FILE_BYTES = 5 * 1024 * 1024
GENERAL_WASTE = "Buitinės atliekos"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _read_rows(response: Any, source: BaseSource | None) -> tuple[str, list[list[str]]]:
    """The first sheet's name and its rows as stripped texts, empty rows dropped."""
    # Raw numbers (dates=False), as the cells were read before the shared parser.
    sheet = XlsxParser(dates=False, max_bytes=MAX_FILE_BYTES).read(response, source)
    rows = []
    for row in sheet.rows:
        texts = ["" if value is None else str(value).strip() for value in row]
        while texts and not texts[-1]:
            texts.pop()
        if texts:
            rows.append(texts)
    return sheet.name, rows


def _village_matches(cell: str, village: str, street: str | None) -> bool:
    name, _, rest = cell.partition("(")
    if _norm(name) != _norm(village):
        return False
    if not street:
        return True
    return _norm(street) in _norm(rest)


def parse_schedule(
    response: Any,
    village: str,
    street: str | None = None,
    source: BaseSource | None = None,
) -> list[dict[str, Any]]:
    title, rows = _read_rows(response, source)
    year_match = re.search(r"\b(20\d{2})\b", title)
    if not year_match:
        raise ValueError("Year not found in XLSX sheet name")
    year = int(year_match.group(1))
    header_idx = next(
        (i for i, r in enumerate(rows) if any(_norm(c) == "kaimai" for c in r)), None
    )
    if header_idx is None:
        raise ValueError(
            "Header row not found in XLSX; the file format may have changed"
        )
    header = rows[header_idx]
    # The header cells are merged inconsistently; the village/street name is
    # always the column directly left of the weekday column.
    weekday_col = next(
        (i for i, c in enumerate(header) if _norm(c).startswith("savaitės")), None
    )
    if not weekday_col:
        raise ValueError("Weekday column not found in XLSX header")
    village_col = weekday_col - 1
    month_cols = {
        i: month for i, c in enumerate(header) if (month := recurrence.month(c))
    }
    entries: list[dict[str, Any]] = []
    known: list[str] = []
    for row in rows[header_idx + 1 :]:
        if len(row) <= village_col or not row[village_col]:
            continue
        known.append(row[village_col].partition("(")[0].strip())
        if not _village_matches(row[village_col], village, street):
            continue
        for col, month in month_cols.items():
            if col >= len(row):
                continue
            for day in re.findall(r"(\d{1,2})\s*d", row[col]):
                entries.append(
                    {"date": dt.date(year, month, int(day)), "type": GENERAL_WASTE}
                )
        if entries:
            break
    if not entries:
        raise SourceArgumentNotFoundWithSuggestions(
            "village", village, sorted(set(known))
        )
    return entries


class NemenkomParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Nemenkom parser requires a source")
        return parse_schedule(
            response, source.params["village"], source.params.get("street"), source
        )
