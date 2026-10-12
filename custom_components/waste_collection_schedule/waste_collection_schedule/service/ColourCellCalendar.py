"""Pipeline components for colour-coded month-column PDF calendars.

Some French intercommunalités (Pays de Craon) publish one annual PDF laid out as
14 month columns (January of the year to February of the next). Every day is a
row ``<weekday initial> <day number> [text]`` painted in a background colour
that says what is collected that week, as explained by a legend: household
waste, packaging, a public holiday (green, or marked ``*``) and a special
collection such as branch shredding (blue, the municipalities named in the row).

:class:`ColourCellCalendarParser` reads such a PDF and returns one
:class:`CalendarDay` per painted row. The year is not printed beside the
columns; it is part of the PDF's file name (``calendrier-collecte-2026.pdf``),
so it comes from the response URL. Every cell is checked against the calendar
(the day must exist in that month and fall on the printed weekday initial), so a
changed layout fails loudly instead of shifting dates.

What a category *means* for a household (which weekday, how a holiday shifts the
collection) is left to the source's ``preprocess``.
"""

from __future__ import annotations

import colorsys
import datetime
import re
from io import BytesIO
from typing import TYPE_CHECKING, NamedTuple

from waste_collection_schedule import response_shape

if TYPE_CHECKING:
    from curl_cffi.requests import Response

    from waste_collection_schedule.base_source import BaseSource

#: Cell categories, named after the legend colours.
GENERAL = "general"  # bordeaux / magenta
PACKAGING = "packaging"  # yellow / orange
HOLIDAY = "holiday"  # green, or a cell carrying ``*``
SPECIAL = "special"  # blue

#: Weekday initials as printed, Monday to Sunday.
WEEKDAY_INITIALS = "LMMJVSD"

_YEAR_RE = re.compile(r"(?<!\d)(20\d{2})(?!\d)")


class CalendarDay(NamedTuple):
    """One painted calendar row."""

    date: datetime.date
    category: str
    extra: str  # text after the day number (the municipalities of a special day)


def _to_rgb(color) -> tuple[float, float, float] | None:
    if color is None:
        return None
    if isinstance(color, (int, float)):
        color = (color,)
    try:
        values = [float(v) for v in color]
    except (TypeError, ValueError):
        return None
    if len(values) == 1:
        return (values[0], values[0], values[0])
    if len(values) == 3:
        return (values[0], values[1], values[2])
    if len(values) == 4:
        c, m, y, k = values
        return ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
    return None


def classify_color(color) -> str | None:
    """Map a cell background colour to its legend category, or None."""
    rgb = _to_rgb(color)
    if rgb is None:
        return None
    hue, saturation, value = colorsys.rgb_to_hsv(*rgb)
    if saturation < 0.4 or value < 0.3:
        return None
    if hue >= 0.83 or hue < 0.04:
        return GENERAL
    if 0.05 <= hue < 0.19:
        return PACKAGING
    if 0.19 <= hue < 0.47:
        return HOLIDAY
    if 0.52 <= hue < 0.75:
        return SPECIAL
    return None


def _walk(obj, chars: list, shapes: list) -> None:
    from pdfminer.layout import LTChar, LTCurve

    if isinstance(obj, LTChar):
        chars.append(obj)
    elif isinstance(obj, LTCurve):
        if obj.fill:
            shapes.append(obj)
    elif hasattr(obj, "__iter__"):
        for child in obj:
            _walk(child, chars, shapes)


def _chars_to_text(chars: list) -> str:
    text = ""
    last = None
    for c in sorted(chars, key=lambda c: c.x0):
        if last is not None and c.x0 - last.x1 > 0.3 * max(c.width, 1):
            text += " "
        text += c.get_text()
        last = c
    return text.strip()


class ColourCellCalendarParser:
    """Read a colour-coded month-column PDF calendar into :class:`CalendarDay`s.

    Args:
        year_pattern: regex whose first group is the calendar's first year, searched
            in the response URL.
        min_cells: fewest painted cells expected; fewer means an image-only or
            re-designed PDF and raises ``ResponseShapeError``.
    """

    def __init__(
        self,
        *,
        year_pattern: str = r"calendrier-collecte-(\d{4})",
        min_cells: int = 100,
    ):
        self.year_pattern = re.compile(year_pattern, re.IGNORECASE)
        self.min_cells = min_cells

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[CalendarDay]:
        from pdfminer.high_level import extract_pages

        source_name = response_shape.source_name(source)
        url = str(getattr(response, "url", "") or "")
        match = self.year_pattern.search(url) or _YEAR_RE.search(url)
        response_shape.expect(
            match is not None,
            source_name=source_name,
            detail=f"no calendar year in PDF URL {url}",
            raw=url,
        )
        assert match is not None
        year = int(match.group(1))

        cells = []  # (page, x0, day, initial, category, extra)
        for page_no, page in enumerate(extract_pages(BytesIO(response.content))):
            chars: list = []
            shapes: list = []
            _walk(page, chars, shapes)
            for shape in shapes:
                width, height = shape.width, shape.height
                if not (25 < width < 130 and 6 < height < 18 and width > 3 * height):
                    continue
                category = classify_color(shape.non_stroking_color)
                if category is None:
                    continue
                inside = sorted(
                    (
                        c
                        for c in chars
                        if shape.x0 <= (c.x0 + c.x1) / 2 <= shape.x1
                        and shape.y0 <= (c.y0 + c.y1) / 2 <= shape.y1
                        and c.get_text().strip()
                    ),
                    key=lambda c: c.x0,
                )
                day_chars: list = []
                for c in inside:
                    if c.get_text().isdigit():
                        if day_chars and c.x0 - day_chars[-1].x1 > max(c.width, 1):
                            break
                        day_chars.append(c)
                    elif day_chars:
                        break
                if not day_chars:
                    continue  # legend box or similar
                letters = [
                    c
                    for c in inside
                    if c.x1 <= day_chars[0].x0 + 0.5 and c.get_text().isalpha()
                ]
                initial = letters[-1].get_text().upper() if letters else ""
                if any(c.get_text() == "*" for c in inside):
                    category = HOLIDAY
                rest = [
                    c
                    for c in inside
                    if c.x0 > day_chars[-1].x1 - 0.5 and c.get_text() != "*"
                ]
                extra = re.sub(r"\bS\.\s?\d+\b", "", _chars_to_text(rest)).strip()
                cells.append(
                    (
                        page_no,
                        shape.x0,
                        int("".join(c.get_text() for c in day_chars)),
                        initial,
                        category,
                        extra,
                    )
                )

        response_shape.expect(
            len(cells) >= self.min_cells,
            source_name=source_name,
            detail=f"calendar PDF yielded {len(cells)} painted cells, under {self.min_cells}",
            raw=url,
        )

        # Group cells into month columns in reading order (page, then x position).
        columns: list[list[tuple]] = []
        for cell in sorted(cells, key=lambda c: (c[0], c[1])):
            if (
                columns
                and columns[-1][0][0] == cell[0]
                and abs(columns[-1][0][1] - cell[1]) < 10
            ):
                columns[-1].append(cell)
            else:
                columns.append([cell])

        days: list[CalendarDay] = []
        for index, column in enumerate(columns):
            col_year = year + index // 12
            col_month = index % 12 + 1
            for _, _, day, initial, category, extra in column:
                try:
                    date = datetime.date(col_year, col_month, day)
                except ValueError:
                    response_shape.expect(
                        False,
                        source_name=source_name,
                        detail=f"invalid date {col_year}-{col_month}-{day} in calendar PDF",
                        raw=url,
                    )
                    raise
                response_shape.expect(
                    not initial or initial == WEEKDAY_INITIALS[date.weekday()],
                    source_name=source_name,
                    detail=f"weekday mismatch for {date.isoformat()} in calendar PDF",
                    raw=url,
                )
                days.append(CalendarDay(date, category, extra))
        return days
