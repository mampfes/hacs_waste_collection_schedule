"""Read dated month grids with coloured cells, rings, or day numerals."""

from __future__ import annotations

import datetime
import re
import statistics
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from io import BytesIO
from itertools import pairwise
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


def _normal(value: str) -> str:
    return " ".join(
        "".join(
            c
            for c in unicodedata.normalize("NFKD", value)
            if not unicodedata.combining(c)
        )
        .upper()
        .split()
    )


def _rgb(value: Any) -> tuple[float, float, float] | None:
    if isinstance(value, (int, float)):
        return float(value), float(value), float(value)
    if not isinstance(value, (tuple, list)) or not all(
        isinstance(n, (int, float)) for n in value
    ):
        return None
    if len(value) == 1:
        return float(value[0]), float(value[0]), float(value[0])
    if len(value) == 3:
        return float(value[0]), float(value[1]), float(value[2])
    if len(value) == 4:
        c, m, y, k = value
        return (1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k)
    return None


@dataclass(frozen=True)
class _Word:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    color: Any

    @property
    def x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def y(self) -> float:
        return (self.y0 + self.y1) / 2


def _walk(item):
    yield item
    if hasattr(item, "__iter__"):
        for child in item:
            yield from _walk(child)


def _words(line):
    from pdfminer.layout import LTChar

    pending = []

    def flush():
        if not pending:
            return None
        word = _Word(
            "".join(c.get_text() for c in pending),
            min(c.x0 for c in pending),
            min(c.y0 for c in pending),
            max(c.x1 for c in pending),
            max(c.y1 for c in pending),
            pending[0].graphicstate.ncolor,
        )
        pending.clear()
        return word

    for child in line:
        if not isinstance(child, LTChar) or child.get_text().isspace():
            word = flush()
            if word is not None:
                yield word
        else:
            if pending and child.x0 - pending[-1].x1 > max(child.width, 1) * 0.8:
                word = flush()
                if word is not None:
                    yield word
            pending.append(child)
    word = flush()
    if word is not None:
        yield word


def _rows(words: Sequence[_Word], tolerance: float = 5) -> list[list[_Word]]:
    rows: list[list[_Word]] = []
    for word in sorted(words, key=lambda w: -w.y):
        if not rows or abs(word.y - statistics.mean(w.y for w in rows[-1])) > tolerance:
            rows.append([])
        rows[-1].append(word)
    return rows


def _outline(shape) -> list[tuple[float, float]] | None:
    """Approximate a single, solid path; compound rings cannot hide its centre."""
    path = getattr(shape, "original_path", None)
    if not path:
        return [
            (shape.x0, shape.y0),
            (shape.x1, shape.y0),
            (shape.x1, shape.y1),
            (shape.x0, shape.y1),
        ]
    if sum(part[0] == "m" for part in path) != 1:
        return None
    points = []
    current = None
    for part in path:
        if part[0] in ("m", "l"):
            current = part[1]
            points.append(current)
        elif part[0] == "c" and current is not None:
            a, b, end = part[1:]
            start = current
            for index in range(1, 17):
                t = index / 16
                points.append(
                    tuple(
                        (1 - t) ** 3 * start[axis]
                        + 3 * (1 - t) ** 2 * t * a[axis]
                        + 3 * (1 - t) * t * t * b[axis]
                        + t**3 * end[axis]
                        for axis in (0, 1)
                    )
                )
            current = end
    return points


def _covered(earlier, later) -> bool:
    """Later solid fills hide earlier markers only if their whole path fits."""
    if not later.fill or not (
        later.x0 <= earlier.x0 + 0.1
        and later.y0 <= earlier.y0 + 0.1
        and later.x1 >= earlier.x1 - 0.1
        and later.y1 >= earlier.y1 - 0.1
    ):
        return False
    outer, inner = _outline(later), _outline(earlier)
    if not outer or not inner:
        return False
    from waste_collection_schedule.service.ArcGis import point_in_polygon

    def inside(point):
        x, y = point
        for a, b in zip(outer, outer[1:] + outer[:1], strict=True):
            dx, dy = b[0] - a[0], b[1] - a[1]
            t = (
                max(
                    0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy))
                )
                if dx or dy
                else 0
            )
            if (x - a[0] - t * dx) ** 2 + (y - a[1] - t * dy) ** 2 <= 0.15**2:
                return True
        return point_in_polygon(x, y, outer)

    return all(inside(point) for point in inner)


class MarkedPdfCalendarParser(Parser[list[dict[str, Any]]]):
    """Read dates from printed month/weekday/day grids, with no inferred cadence.

    All matching markers are read, including concentric colours for combined
    services. ``font_colors`` additionally recognises coloured day numerals.
    Month cells are checked against their printed weekday and row position;
    neighbouring-month padding is ignored. ``alignment`` describes the month
    heading, not the dates. The complete calendar text is carried for a source
    to apply published route restrictions without inventing local rules.
    ``pages`` can restrict a document to its calendar pages. With
    ``allow_unmarked_missing_days``, blank holiday cells are accepted only when
    their inferred position carries no collection marker.

    stroke_colors optionally separates outlined symbols from filled symbols.
    max_duplicate_day_repairs permits a bounded number of duplicated numerals
    to use their complete weekday-grid position when that number is missing.
    month_heading_pattern optionally reads numeric headings via a named month
    group (and an optional year group, checked against the printed year).

    Set row_bands=True for filled week rows spanning several day cells.
    heading_year accepts a year suffix on each month heading. day_font_size
    restricts the numeral height in PDF points, for files carrying invisible
    editing text in a different font size; all expected days are still required.
    """

    def __init__(
        self,
        *,
        months: Sequence[str],
        weekdays: Sequence[str],
        year_pattern: str,
        colors: Mapping[str, Sequence[tuple[float, ...]]],
        font_colors: Mapping[str, Sequence[tuple[float, ...]]] | None = None,
        stroke_colors: Mapping[str, Sequence[tuple[float, ...]]] | None = None,
        month_heading_pattern: str | None = None,
        alignment: str = "center",
        tolerance: float = 0.12,
        allow_unmarked_missing_days: bool = False,
        pages: Sequence[int] | None = None,
        cancelled_colors: Sequence[tuple[float, ...]] = (),
        max_duplicate_day_repairs: int = 0,
        row_bands: bool = False,
        heading_year: bool = False,
        day_font_size: tuple[float, float] | None = None,
    ):
        self.months = {_normal(name): i + 1 for i, name in enumerate(months)}
        self.month_heading_pattern = (
            re.compile(month_heading_pattern) if month_heading_pattern else None
        )
        self.weekdays = tuple(_normal(name) for name in weekdays)
        self.year_pattern = re.compile(year_pattern)
        self.colors = dict(colors)
        self.font_colors = dict(font_colors or {})
        self.stroke_colors = (
            dict(stroke_colors) if stroke_colors is not None else self.colors
        )
        if alignment not in ("left", "center"):
            raise ValueError("Unknown month-heading alignment")
        self.alignment = alignment
        self.tolerance = tolerance
        self.allow_unmarked_missing_days = allow_unmarked_missing_days
        self.pages = frozenset(pages) if pages is not None else None
        self.cancelled_colors = {"cancelled": tuple(cancelled_colors)}
        if max_duplicate_day_repairs < 0:
            raise ValueError("Duplicate-day repair limit cannot be negative")
        self.max_duplicate_day_repairs = max_duplicate_day_repairs
        self.row_bands = row_bands
        self.heading_year = heading_year
        self.day_font_size = day_font_size

    def _keys(
        self, color: Any, palette: Mapping[str, Sequence[tuple[float, ...]]]
    ) -> set[str]:
        rgb = _rgb(color)
        if rgb is None:
            return set()
        return {
            key
            for key, samples in palette.items()
            if any(
                (sample_rgb := _rgb(sample)) is not None
                and sum((a - b) ** 2 for a, b in zip(rgb, sample_rgb, strict=True))
                ** 0.5
                <= self.tolerance
                for sample in samples
            )
        }

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTCurve, LTTextLine

        pages = []
        heading_years: set[int] = set()
        for page in extract_pages(BytesIO(response.content), page_numbers=self.pages):
            objects = list(_walk(page))
            lines = [obj for obj in objects if isinstance(obj, LTTextLine)]
            words = [word for line in lines for word in _words(line)]
            headings = []
            for line in lines:
                heading_text = _normal(line.get_text())
                match = (
                    self.month_heading_pattern.fullmatch(heading_text)
                    if self.month_heading_pattern
                    else None
                )
                if match:
                    heading_month: int | None = int(match["month"])
                    if match.groupdict().get("year"):
                        heading_years.add(int(match["year"]))
                else:
                    if self.heading_year:
                        heading_text = re.sub(r"\s+20\d{2}$", "", heading_text)
                    heading_month = self.months.get(heading_text)
                if heading_month is not None:
                    headings.append(
                        _Word(
                            str(heading_month), line.x0, line.y0, line.x1, line.y1, None
                        )
                    )
            pages.append(
                (
                    words,
                    headings,
                    [
                        obj
                        for obj in objects
                        if isinstance(obj, LTCurve) and (obj.fill or obj.stroke)
                    ],
                )
            )
        text = "\n".join(" ".join(w.text for w in words) for words, _, _ in pages)
        match = self.year_pattern.search(_normal(text))
        if match is None:
            raise ValueError("Printed calendar year not found")
        year = int(match.group(1))
        if heading_years and heading_years != {year}:
            raise ValueError("Month headings disagree with the printed calendar year")
        seen_months: set[int] = set()
        cancelled: set[datetime.date] = set()
        results: dict[tuple[datetime.date, str], dict[str, Any]] = {}
        repaired_days = 0
        for words, headings, shapes in pages:
            heading_rows = _rows(headings)
            row_steps = [
                statistics.mean(w.y for w in a) - statistics.mean(w.y for w in b)
                for a, b in pairwise(heading_rows)
            ]
            row_step = statistics.median(row_steps) if row_steps else 180
            for row_index, heading_row in enumerate(heading_rows):
                ordered = sorted(heading_row, key=lambda w: w.x)
                anchors = [w.x0 if self.alignment == "left" else w.x for w in ordered]
                step = (
                    statistics.median(b - a for a, b in pairwise(anchors))
                    if len(anchors) > 1
                    else 150
                )
                for index, heading in enumerate(ordered):
                    month = int(heading.text)
                    if month in seen_months:
                        raise ValueError("Calendar repeats a printed month")
                    seen_months.add(month)
                    if self.alignment == "left":
                        left, right = (
                            anchors[index] - 2,
                            (
                                anchors[index + 1] - 2
                                if index + 1 < len(anchors)
                                else anchors[index] + step - 2
                            ),
                        )
                    else:
                        left = (
                            (anchors[index - 1] + anchors[index]) / 2
                            if index
                            else anchors[index] - step / 2
                        )
                        right = (
                            (anchors[index + 1] + anchors[index]) / 2
                            if index + 1 < len(anchors)
                            else anchors[index] + step / 2
                        )
                    headers = [
                        w
                        for w in words
                        if left <= w.x < right
                        and heading.y0 - 35 < w.y < heading.y0
                        and _normal(w.text) in self.weekdays
                    ]
                    header_rows = _rows(headers)
                    header = next(
                        (
                            sorted(row, key=lambda w: w.x)
                            for row in header_rows
                            if tuple(
                                _normal(w.text) for w in sorted(row, key=lambda w: w.x)
                            )
                            == self.weekdays
                        ),
                        None,
                    )
                    if header is None:
                        raise ValueError(f"Weekday grid missing for month {month}")
                    centers = [w.x for w in header]
                    cell_width = statistics.median(b - a for a, b in pairwise(centers))
                    top = min(w.y0 for w in header) - 1
                    bottom = (
                        statistics.mean(w.y for w in heading_rows[row_index + 1])
                        if row_index + 1 < len(heading_rows)
                        else heading.y - row_step
                    ) + 10
                    numbers = [
                        w
                        for w in words
                        if left <= w.x < right
                        and bottom < w.y < top
                        and (
                            w.text == "X"
                            or (w.text.isdigit() and 1 <= int(w.text) <= 31)
                        )
                        and min(abs(w.x - x) for x in centers) < cell_width * 0.45
                        and (
                            self.day_font_size is None
                            or self.day_font_size[0]
                            <= w.y1 - w.y0
                            <= self.day_font_size[1]
                        )
                    ]
                    day_rows = _rows(numbers)
                    printed_days = [int(w.text) for w in numbers if w.text != "X"]
                    first_weekday = datetime.date(year, month, 1).weekday()
                    read_days: set[int] = set()
                    row_offset = (
                        1
                        if first_weekday >= len(self.weekdays)
                        and day_rows
                        and any(
                            w.text.isdigit() and int(w.text) <= 7 for w in day_rows[0]
                        )
                        else 0
                    )
                    for week, day_row in enumerate(day_rows, start=row_offset):
                        for word in day_row:
                            column = min(
                                range(len(centers)),
                                key=lambda i: abs(centers[i] - word.x),
                            )
                            day = week * 7 + column - first_weekday + 1
                            try:
                                date = datetime.date(year, month, day)
                            except ValueError:
                                continue
                            if word.text == "X":
                                cancelled.add(date)
                                read_days.add(day)
                                continue
                            if int(word.text) != day:
                                if (
                                    repaired_days >= self.max_duplicate_day_repairs
                                    or printed_days.count(int(word.text)) < 2
                                    or day in printed_days
                                ):
                                    raise ValueError(
                                        f"Printed day {word.text} differs from grid date {date}"
                                    )
                                # One duplicated numeral can be dated from the
                                # complete weekday grid and its missing number.
                                # Never repair an arbitrary or shifted layout.
                                repaired_days += 1
                            read_days.add(day)
                            keys = self._keys(word.color, self.font_colors)
                            candidates = [
                                shape
                                for shape in shapes
                                if 1
                                < shape.width
                                < cell_width * (7.2 if self.row_bands else 1.6)
                                and 1 < shape.height < cell_width * 1.6
                                and min(shape.x1, word.x1) - max(shape.x0, word.x0)
                                > 0.1
                                and min(shape.y1, word.y1) - max(shape.y0, word.y0)
                                > 0.1
                            ]
                            for index, shape in enumerate(candidates):
                                if any(
                                    _covered(shape, later)
                                    for later in candidates[index + 1 :]
                                ):
                                    continue
                                if shape.fill:
                                    keys.update(
                                        self._keys(
                                            shape.non_stroking_color, self.colors
                                        )
                                    )
                                if shape.stroke:
                                    keys.update(
                                        self._keys(
                                            shape.stroking_color, self.stroke_colors
                                        )
                                    )
                            for key in sorted(keys):
                                results[(date, key)] = {
                                    "date": date,
                                    "type": key,
                                    "calendar_text": text,
                                }
                    expected = {
                        day
                        for day in range(1, 32)
                        if _valid_weekday(year, month, day, len(self.weekdays))
                    }
                    missing = expected - read_days
                    if missing and self.allow_unmarked_missing_days:
                        for day in missing:
                            week = (day + first_weekday - 1) // 7 - row_offset
                            if not 0 <= week < len(day_rows):
                                raise ValueError("Missing calendar week")
                            x = centers[datetime.date(year, month, day).weekday()]
                            y = statistics.mean(w.y for w in day_rows[week])
                            if any(
                                1 < shape.width < cell_width * 1.6
                                and 1 < shape.height < cell_width * 1.6
                                and shape.x0 <= x <= shape.x1
                                and shape.y0 <= y <= shape.y1
                                and shape.fill
                                and self._keys(
                                    shape.non_stroking_color, self.cancelled_colors
                                )
                                for shape in shapes
                            ):
                                cancelled.add(datetime.date(year, month, day))
                                continue
                            for shape in shapes:
                                if (
                                    1 < shape.width < cell_width * 1.6
                                    and 1 < shape.height < cell_width * 1.6
                                    and shape.x0 <= x <= shape.x1
                                    and shape.y0 <= y <= shape.y1
                                    and (
                                        (
                                            shape.fill
                                            and self._keys(
                                                shape.non_stroking_color, self.colors
                                            )
                                        )
                                        or (
                                            shape.stroke
                                            and self._keys(
                                                shape.stroking_color, self.stroke_colors
                                            )
                                        )
                                    )
                                ):
                                    raise ValueError(
                                        f"Collection marker has no printed day at {year}-{month}-{day}"
                                    )
                    elif missing:
                        raise ValueError(
                            f"Incomplete printed grid for month {month}: {len(read_days)} days, expected {len(expected)}"
                        )
        if seen_months != set(range(1, 13)) or not results:
            raise ValueError("PDF carries no complete annual collection calendar")
        marked_dates = sorted({day for day, _ in results})
        next_marked = {
            day: next(
                (candidate for candidate in marked_dates if candidate > day), None
            )
            for day in sorted(cancelled)
        }
        for record in results.values():
            record["cancelled_dates"] = tuple(sorted(cancelled))
            record["next_marked_after_cancelled"] = next_marked
        return [results[key] for key in sorted(results)]


def _valid_weekday(year: int, month: int, day: int, columns: int) -> bool:
    try:
        return datetime.date(year, month, day).weekday() < columns
    except ValueError:
        return False
