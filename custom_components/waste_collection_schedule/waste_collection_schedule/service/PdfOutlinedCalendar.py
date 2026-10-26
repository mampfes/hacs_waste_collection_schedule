"""Read a PDF calendar whose day numbers are outlines and whose rounds are text.

Some printed calendars (InDesign exports with the fonts converted to curves)
keep only the round labels as text: the month names over the columns and the
"1 V", "2 S" day numbers down each column are vector glyphs. Plain text
extraction then yields a stream of "UMIDO", "CARTA", ... with nothing to date
them. Their positions still do:

* the day rows are a regular lattice of glyph rows (day number and weekday
  letter), the longest run of glyph rows at one spacing;
* the month columns are headed by a row of glyph runs (the outlined month
  names) just above the lattice, one run per column;
* a label belongs to the column whose heading is nearest and to the day row
  level with it.

:class:`OutlinedDayRowsParser` reads that from a
:class:`~waste_collection_schedule.parsers.PdfWordLayoutParser` layout and
yields ``(date, label)`` rows for an ``ICSTransformer``. The months run on from
``first_month`` across the columns and pages in reading order, and the year
comes from ``year_pattern``. Every column's glyphs must stop at its month's
last day (no glyphs on 29 to 31 February), which checks the month order and
the year's leap day, so a misread page fails loudly instead of shifting the
schedule.
"""

from __future__ import annotations

import calendar
import datetime
import itertools
import re
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

from waste_collection_schedule import response_shape
from waste_collection_schedule.parsers import (
    Parser,
    PdfVector,
    PdfWordLayout,
    PdfWordLayoutParser,
)

if TYPE_CHECKING:
    from curl_cffi.requests import Response

    from waste_collection_schedule.base_source import BaseSource

_YEAR_RE = re.compile(r"(?<!\d)(20\d{2})(?!\d)")


def _clusters(values: Iterable[float], tolerance: float) -> list[list[float]]:
    """Sorted values grouped where neighbours are within ``tolerance``."""
    groups: list[list[float]] = []
    for value in sorted(values):
        if groups and value - groups[-1][-1] <= tolerance:
            groups[-1].append(value)
        else:
            groups.append([value])
    return groups


def _lattice(ys: list[float], min_rows: int) -> list[float]:
    """The longest run of rows at one spacing, top first (PDF y grows up)."""
    rows = sorted((sum(g) / len(g) for g in _clusters(ys, 2.0)), reverse=True)
    best: list[float] = []
    for start in range(len(rows)):
        for second in range(start + 1, min(start + 4, len(rows))):
            pitch = rows[start] - rows[second]
            if pitch < 5:
                continue
            run = [rows[start], rows[second]]
            for y in rows[second + 1 :]:
                gap = run[-1] - y
                if abs(gap - pitch) <= 1.5:
                    run.append(y)
                elif gap > pitch + 1.5:
                    break
            if len(run) > len(best):
                best = run
    return best if len(best) >= min_rows else []


def _median_gap(centres: Sequence[float]) -> float:
    gaps = sorted(b - a for a, b in itertools.pairwise(centres))
    return gaps[(len(gaps) - 1) // 2] if gaps else 0.0


def _nearest(centres: Sequence[float], spacing: float, x: float) -> int | None:
    """The heading over ``x``: the nearest, if within its column's width."""
    if not centres:
        return None
    nearest = min(range(len(centres)), key=lambda i: abs(centres[i] - x))
    return nearest if abs(centres[nearest] - x) <= 0.6 * spacing else None


class OutlinedDayRowsParser(Parser["list[tuple[datetime.date, str]]"]):
    """Date the text labels of a day-row calendar with outlined day numbers.

    Args:
        labels: the round labels printed in the day cells, compared
            case-insensitively with each word. Pass the transformer's
            ``type_value_map``.
        year_pattern: a regex whose first group is the calendar's year,
            searched in the PDF text and then in the response URL; without
            one, the first ``20xx`` found.
        first_month: the month of the first column of the first page.
        glyph_height: the height range (points) of a day-number glyph.
        glyph_width: the widest a day-number glyph may be (points).
        min_labels: fewest dated labels expected; fewer raise
            ``ResponseShapeError`` (a changed design).
    """

    def __init__(
        self,
        labels: Iterable[str],
        *,
        year_pattern: str | None = None,
        first_month: int = 1,
        glyph_height: tuple[float, float] = (6.0, 9.5),
        glyph_width: float = 9.0,
        min_labels: int = 20,
    ):
        self.labels = {label.casefold(): label for label in labels}
        self.year_re = re.compile(year_pattern, re.IGNORECASE) if year_pattern else None
        self.first_month = first_month
        self.glyph_height = glyph_height
        self.glyph_width = glyph_width
        self.min_labels = min_labels

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[tuple[datetime.date, str]]:
        layout = PdfWordLayoutParser(min_words=10)(response, source)[0]
        return self.read(
            layout,
            str(getattr(response, "url", "") or ""),
            response_shape.source_name(source),
        )

    def read(
        self, layout: PdfWordLayout, url: str = "", name: str = "source"
    ) -> list[tuple[datetime.date, str]]:
        """Date the labels of an already parsed layout (``url`` for the year)."""
        year = self._year(" ".join(line.text for line in layout.lines), url)
        response_shape.expect(
            year is not None,
            source_name=name,
            detail="no calendar year in the PDF or its URL",
            raw=url,
        )
        if year is None:
            return []

        rows: set[tuple[datetime.date, str]] = set()
        month_index = 0
        for page in sorted({w.page for w in layout.words}):
            glyphs = [
                v
                for v in layout.vectors
                if v.page == page
                and self.glyph_height[0] <= v.y1 - v.y0 <= self.glyph_height[1]
                and v.x1 - v.x0 <= self.glyph_width
            ]
            lattice = _lattice([(v.y0 + v.y1) / 2 for v in glyphs], 28)
            if not lattice:
                continue
            pitch = (lattice[0] - lattice[-1]) / (len(lattice) - 1)
            centres = self._headings(glyphs, lattice[0], pitch)
            spacing = _median_gap(centres)

            def column(
                x: float, centres: Sequence[float] = centres, spacing: float = spacing
            ) -> int | None:
                return _nearest(centres, spacing, x)

            # A heading over a day column has a glyph on each of its days; a
            # run elsewhere in that row (an outlined legend title) does not.
            day_rows: dict[int, set[int]] = {}
            for v in glyphs:
                row = self._row((v.y0 + v.y1) / 2, lattice, pitch)
                col = column((v.x0 + v.x1) / 2)
                if row is not None and col is not None:
                    day_rows.setdefault(col, set()).add(row)
            kept = [i for i in range(len(centres)) if len(day_rows.get(i, ())) >= 28]
            response_shape.expect(
                len(kept) >= 2,
                source_name=name,
                detail=f"page {page + 1}: no row of month headings over the days",
            )
            months = []
            for _ in kept:
                month0 = self.first_month - 1 + month_index
                months.append((year + month0 // 12, month0 % 12 + 1))
                month_index += 1

            # Each column's glyph rows must end on its month's last day.
            for (y, month), index in zip(months, kept, strict=True):
                length = calendar.monthrange(y, month)[1]
                last = max(day_rows[index]) + 1
                response_shape.expect(
                    last == length,
                    source_name=name,
                    detail=(
                        f"page {page + 1}: a day column ends at {last}, "
                        f"expected {length} for {y}-{month:02d}"
                    ),
                )
            month_of = dict(zip(kept, months, strict=True))

            for word in layout.words:
                if word.page != page:
                    continue
                row = self._row(word.y, lattice, pitch)
                if row is None:
                    continue
                col = column(word.x)
                if col not in month_of:
                    continue
                y, month = month_of[col]
                for token in word.text.split():
                    label = self.labels.get(token.casefold())
                    if label is None:
                        continue
                    try:
                        rows.add((datetime.date(y, month, row + 1), label))
                    except ValueError:
                        continue

        response_shape.expect(
            len(rows) >= self.min_labels,
            source_name=name,
            detail=f"found {len(rows)} dated labels, expected {self.min_labels}+",
            raw=str(layout.lines[:20]),
        )
        return sorted(rows)

    @staticmethod
    def _row(y: float, lattice: list[float], pitch: float) -> int | None:
        """The day row (zero-based) level with ``y``, or None."""
        index = round((lattice[0] - y) / pitch)
        if 0 <= index < len(lattice) and abs(lattice[index] - y) <= pitch / 2:
            return index
        return None

    @staticmethod
    def _headings(glyphs: list[PdfVector], top: float, pitch: float) -> list[float]:
        """The x centres of the outlined month names heading the columns.

        They are the glyph row nearest above the first day row, within two
        and a half rows (letters of one name may sit a few points apart);
        each name is a run of glyphs apart from the next by a wide gap.
        """
        above = [
            v for v in glyphs if pitch / 2 < (v.y0 + v.y1) / 2 - top <= 2.5 * pitch
        ]
        if not above:
            return []
        lowest = min((v.y0 + v.y1) / 2 for v in above)
        heading = [v for v in above if (v.y0 + v.y1) / 2 - lowest <= pitch / 2]
        runs: list[list[PdfVector]] = []
        for v in sorted(heading, key=lambda v: v.x0):
            if runs and v.x0 - max(r.x1 for r in runs[-1]) <= 3 * pitch / 4:
                runs[-1].append(v)
            else:
                runs.append([v])
        return [(min(v.x0 for v in run) + max(v.x1 for v in run)) / 2 for run in runs]

    def _year(self, text: str, url: str) -> int | None:
        for haystack in (text, url):
            if self.year_re and (match := self.year_re.search(haystack)):
                return int(match.group(1))
        for haystack in (text, url):
            if match := _YEAR_RE.search(haystack):
                return int(match.group(1))
        return None
