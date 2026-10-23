"""Pipeline component for a PDF planning that lists dates per group of places.

Some intercommunal bodies publish their one-off rounds (green waste, bulky
items) as a single poster: one column per round, and in each column blocks of
place names with the dates they share::

    DÉCHETS VERTS                          ENCOMBRANTS

    AYGUEMORTE-LES-GRAVES   8 avril*       BEAUTIRAN        23 avril
            BEAUTIRAN       9 juin     CASTRES-GIRONDE      15 octobre
      CASTRES-GIRONDE       6 octobre

A block is the run of lines between blank lines; its places are those named in
any line of it, its dates those written in any line of it (a day number
followed by a month name). The text layer only keeps the columns apart in
``pypdf``'s *layout* mode, so this reads that, cuts every line at the column
headers' positions and parses each column on its own.

The place names cannot be told from other capitalised text, so the source
passes the names it expects (:class:`PlaceDate` rows are produced only for
those). Names are compared ignoring case, accents and hyphens, and the row
carries the name as the source spelled it. The year is printed once in the
poster's title (``year_pattern``), which also fails loudly when the poster
changes shape. ``label`` is a plain string for the source's transformer to map.
"""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING, Any, NamedTuple

from waste_collection_schedule import lookups, recurrence, response_shape
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from waste_collection_schedule.base_source import BaseSource

# "8 avril", "23 avril*", "17 novembre": a day number, then a month name.
_DAY_MONTH = re.compile(r"(\d{1,2})\s*([^\W\d_]+)")


class PlaceDate(NamedTuple):
    """One dated entry of a column: the place, the column's label and the day."""

    place: str
    label: str
    date: date


def dates_in(text: str, year: int) -> list[date]:
    """The ``<day> <month name>`` dates written in ``text``, in the given year."""
    found: list[date] = []
    for match in _DAY_MONTH.finditer(text):
        month = recurrence.month(match.group(2))
        if month is None:
            continue
        try:
            found.append(date(year, month, int(match.group(1))))
        except ValueError:
            continue
    return found


def places_in(text: str, places: Sequence[str]) -> list[str]:
    """The ``places`` named in ``text``, ignoring case, accents and hyphens."""
    haystack = f" {lookups.normalize_loose(text)} "
    return [
        place for place in places if f" {lookups.normalize_loose(place)} " in haystack
    ]


def column_bounds(
    header_line: str, headers: Sequence[str], margin: int
) -> list[tuple[int, int | None]]:
    """``[start, end)`` character ranges of the columns under a header line.

    The first column starts at 0; every other starts ``margin`` characters left
    of its header, because the places under it may begin slightly before it.
    """
    starts = [0]
    for header in headers[1:]:
        starts.append(max(header_line.index(header) - margin, 0))
    ends: list[int | None] = [*starts[1:], None]
    return list(zip(starts, ends, strict=True))


def parse_column(
    lines: Sequence[str], label: str, places: Sequence[str], year: int
) -> list[PlaceDate]:
    """Read one column's lines: every blank-line block pairs its places and dates."""
    rows: list[PlaceDate] = []
    block: list[str] = []

    def commit() -> None:
        text = "\n".join(block)
        for place in places_in(text, places):
            rows.extend(
                PlaceDate(place, label, found) for found in dates_in(text, year)
            )
        block.clear()

    for line in lines:
        if line.strip():
            block.append(line.strip())
        else:
            commit()
    commit()
    return rows


class PlaceColumnsParser(Parser["list[PlaceDate]"]):
    """Read a layout-mode PDF poster of place blocks and dates, one column per round.

    Args:
        places: the place names to look for (see the module docstring).
        columns: ``{label: header text}`` in left-to-right order; the header
            text is how the round's column is titled on the poster, and the
            label is what its rows are tagged with. The headers share one
            line, which starts with the first (a title that merely mentions
            them is not that line).
        year_pattern: regex whose first group is the poster's four-digit year.
        margin: how many characters left of a header its column's places may
            start (default 4).
    """

    def __init__(
        self,
        places: Sequence[str],
        columns: Mapping[str, str],
        year_pattern: str,
        margin: int = 4,
    ):
        self._places = tuple(places)
        self._columns = dict(columns)
        self._year = re.compile(year_pattern)
        self._margin = margin

    def rows(self, text: str, source: BaseSource | None = None) -> list[PlaceDate]:
        """Parse the layout text of the poster (the parser's pure core)."""
        name = response_shape.source_name(source)
        year_match = self._year.search(text)
        response_shape.expect(
            year_match is not None,
            source_name=name,
            detail=f"no year found with {self._year.pattern!r}",
            raw=text[:500],
        )
        year = int(year_match.group(1))  # type: ignore[union-attr]
        headers = list(self._columns.values())
        lines = text.split("\n")
        header_line = next(
            (
                line
                for line in lines
                if line.strip().startswith(headers[0])
                and all(header in line for header in headers)
            ),
            None,
        )
        response_shape.expect(
            header_line is not None,
            source_name=name,
            detail=f"no line with the column headers {headers}",
            raw=text[:500],
        )
        bounds = column_bounds(header_line or "", headers, self._margin)
        rows: list[PlaceDate] = []
        for label, (start, end) in zip(self._columns, bounds, strict=True):
            rows.extend(
                parse_column(
                    [line[start:end] for line in lines], label, self._places, year
                )
            )
        return rows

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[PlaceDate]:
        from io import BytesIO

        from pypdf import PdfReader

        reader = PdfReader(BytesIO(response.content))
        text = "\n".join(
            page.extract_text(extraction_mode="layout") or "" for page in reader.pages
        )
        return self.rows(text, source)
