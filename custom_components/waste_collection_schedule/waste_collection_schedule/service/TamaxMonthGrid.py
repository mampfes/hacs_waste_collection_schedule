"""Read TAMAX household calendars printed as a ruled month-column table.

TAMAX prints most of its household calendars as one table per page: a round
label down the left (``Odpady zmieszane``, ``BIO``, ``SZKŁO``), a column per
month headed by its name (``LIPIEC``), its Roman numeral (``VII``) or, rotated
by 90 degrees, its name read upwards, and in each cell the collection days of
that month (``6; 20``, ``2, 16, 30``). A village or street group sits left of
the labels as a cell merged across all its rows, or the whole page belongs to
one route named in its title::

    parse = RuledTableParser(min_cells=40, merged_cells=True)
    preprocess = MonthGrid(
        _TYPES, year_pattern=r"(20\\d\\d)", areas=_AREAS, area_in="row"
    )
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)

Only days printed in the table are dated. A cell's note in brackets (an
``(za 11.11.2026)`` holiday move, a ``(poniedziałek)`` weekday) is dropped; the
day before it is the printed collection day. A header month earlier than the
one to its left starts the next year, so a sheet running from April to
February dates its last two columns in the following year.
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Literal

from waste_collection_schedule import recurrence, response_shape
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.service.PdfRuledTable import RuledTables

_NOTE = re.compile(r"\([^)]*\)?")
_DAY = re.compile(r"(?<!\d)(\d{1,2})(?!\d)")


def _key(text: str) -> str:
    """Casefold and drop everything but letters and digits."""
    return "".join(ch for ch in text.casefold() if ch.isalnum())


def header_month(cell: str) -> int | None:
    """The month a header cell names, upright or rotated, as a name or numeral."""
    letters = "".join(ch for ch in cell if ch.isalpha())
    if not letters:
        return None
    for candidate in (letters, letters[::-1]):
        number = recurrence.month(candidate, "pl", roman=True)
        if number is not None:
            return number
    return None


class MonthGrid:
    """Date the rounds of TAMAX month-column tables read by ``RuledTableParser``.

    Args:
        labels: the round labels, matched against the start of the label cell
            (the column left of the first month) with case, spaces and
            punctuation ignored, longest first. Pass the
            transformer's ``type_value_map``; the matched key is yielded.
        year_pattern: regex searched in the document text, its first group the
            year of the first month column.
        areas: for a sheet serving several areas, a mapping of the ``area``
            parameter to a regex (case-insensitive) identifying its rows or page.
        area_in: ``"row"`` matches the regex against the cells left of the
            label column, ``"page"`` against the page text.
    """

    def __init__(
        self,
        labels: Iterable[str],
        *,
        year_pattern: str,
        areas: Mapping[str, str] | None = None,
        area_in: Literal["row", "page"] = "row",
    ):
        self._labels = sorted(
            ((_key(label), str(label)) for label in labels),
            key=lambda item: -len(item[0]),
        )
        self._year_re = re.compile(year_pattern)
        self._areas = dict(areas or {})
        self._area_in = area_in

    def __call__(
        self, document: RuledTables, source: BaseSource | None = None
    ) -> Iterable[tuple[datetime.date, str]]:
        name = response_shape.source_name(source)
        match = self._year_re.search(document.text)
        response_shape.expect(
            match is not None,
            source_name=name,
            detail=f"no year matching {self._year_re.pattern!r} in the PDF",
            raw=document.text[:500],
        )
        year = int(match.group(1)) if match else datetime.date.today().year
        area_re = self._area_regex(source)

        results: set[tuple[datetime.date, str]] = set()
        tables = 0
        page_texts = document.page_texts or ("",) * len(document.grids)
        for grid, page_text in zip(document.grids, page_texts, strict=True):
            if area_re is not None and self._area_in == "page":
                if not area_re.search(" ".join(page_text.split())):
                    continue
            columns = self._month_columns(grid, year)
            if columns is None:
                continue
            header, months = columns
            tables += 1
            first = min(months)
            for row in grid[header + 1 :]:
                label = self._label(row[first - 1]) if first else None
                if label is None:
                    continue
                if area_re is not None and self._area_in == "row":
                    area = " ".join(" ".join(row[: first - 1]).split())
                    if not area_re.search(area):
                        continue
                for col, (cell_year, month) in months.items():
                    for day in _DAY.findall(_NOTE.sub(" ", row[col])):
                        try:
                            date = datetime.date(cell_year, month, int(day))
                        except ValueError as err:
                            response_shape.expect(
                                False,
                                source_name=name,
                                detail=f"impossible day {day} in {month}/{cell_year}: {err}",
                                raw=row,
                            )
                            continue
                        results.add((date, label))
        response_shape.expect(
            tables > 0,
            source_name=name,
            detail="no TAMAX month-column table found in the PDF",
            raw=document.text[:500],
        )
        return sorted(results)

    def _area_regex(self, source: BaseSource | None) -> re.Pattern[str] | None:
        if not self._areas:
            return None
        area = getattr(source, "params", {}).get("area") if source else None
        if area not in self._areas:
            raise SourceArgumentNotFoundWithSuggestions("area", area, list(self._areas))
        return re.compile(self._areas[area], re.IGNORECASE)

    def _label(self, cell: str) -> str | None:
        """The label key a round label cell starts with, the longest first."""
        text = _key(cell)
        for key, label in self._labels:
            if text.startswith(key):
                return label
        return None

    @staticmethod
    def _month_columns(
        grid: list[list[str]], year: int
    ) -> tuple[int, dict[int, tuple[int, int]]] | None:
        """The header row index and ``{column: (year, month)}`` of a table."""
        for index, row in enumerate(grid):
            found = {
                col: month
                for col, cell in enumerate(row)
                if (month := header_month(cell)) is not None
            }
            if len(found) < 2:
                continue
            months: dict[int, tuple[int, int]] = {}
            current, previous = year, None
            for col in sorted(found):
                if previous is not None and found[col] < previous:
                    current += 1
                months[col] = (current, found[col])
                previous = found[col]
            return index, months
        return None
