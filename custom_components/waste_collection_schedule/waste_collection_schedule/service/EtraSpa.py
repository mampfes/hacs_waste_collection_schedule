"""Shared pipeline component for ETRA S.p.A.'s InDesign-generated collection calendars.

ETRA (Consorzio di Bacino Brenta, Veneto, Italy) publishes its municipal
collection calendars as a single PDF whose collection-day markers are
vector-drawn circular icons: the PDF has no extractable text layer for the
icons themselves, only their fill colour and position. The page lays out a
3x4 grid of month boxes, each split into "Zona A" / "Zona B" sub-columns, with
a legend mapping each icon colour to a waste type.

``EtraCalendarParser`` reads that layout directly from the PDF's vector
content stream (``pdfminer``), matching each icon to its nearest day number
(by the month's date-column text) and nearest zone sub-column (by position),
rather than any text extraction. Pair it with
``waste_collection_schedule.retrievers.PdfLinkRetriever`` to find the current
year's PDF on the municipality's page, and ``ICSTransformer`` to map the
Italian labels onto canonical WasteTypes.

Some municipalities (e.g. Bassano del Grappa) instead get one PDF per zone
without the "Zona A" / "Zona B" sub-columns; the parser handles that
single-zone layout too (``zone_param=None``).

ETRA's A5 booklet ("CALENDARIO_<Comune>gen_<year>.pdf", e.g. Vigonza) uses
the same icons in a different layout, read by ``EtraBookletParser``: one
month per spread (days 1-12 on the left page, 13-31 on the right), one row
per day, and a column per collection zone plus a glass column whose markers
carry a "Zona N" label for the glass sub-zone collected that day.

Currently used by San Martino di Lupari, Bassano del Grappa and Vigonza, kept
here rather than in the source module because ETRA publishes the identical
templates -- same icon colours, same layouts -- for every municipality in its
consortium; only the PDF URL and the municipality name differ.
"""

from __future__ import annotations

import re
from datetime import date
from io import BytesIO
from typing import TYPE_CHECKING, Any, NamedTuple

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from pdfminer.layout import LTChar, LTCurve, LTPage

    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

_MONTHS = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}
_MONTH_RE = re.compile(r"^(" + "|".join(_MONTHS) + r")\b", re.IGNORECASE)
_DAY_RE = re.compile(r"^(\d{1,2})\s*[A-Z]$")
_YEAR_RE = re.compile(r"CALENDARIO\s+(20\d\d)", re.IGNORECASE)

# RGB fill colours used by the collection symbols in ETRA's InDesign PDFs.
# Part of the shared "Consiglio di Bacino Brenta" template, not per-comune.
COLOUR_MAP: dict[tuple[float, float, float], str] = {
    (0.614, 0.644, 0.681): "Secco residuo",
    (0.993, 0.765, 0.0): "Plastica e metalli",
    (0.0, 0.336, 0.617): "Carta e cartone",
    (0.23, 0.491, 0.202): "Vetro",
    (0.848, 0.736, 0.581): "Verde e ramaglie",
    (0.441, 0.305, 0.26): "Umido organico",
}
_COLOUR_TOLERANCE = 0.01
_MAX_ZONE_DISTANCE = 32
_MAX_DAY_DISTANCE = 7
# Single-zone calendars (one PDF per zone, e.g. Bassano del Grappa) have no
# "ZONA A / ZONA B" sub-headings; the symbols sit in one strip right of the
# day numbers, roughly this far from the date column's right edge.
_SINGLE_ZONE_OFFSET = 22


def _iter_elements(container: Any) -> Any:
    from pdfminer.layout import LTContainer

    for element in container:
        yield element
        if isinstance(element, LTContainer):
            yield from _iter_elements(element)


def _waste_type(
    colour: Any, colours: Mapping[tuple[float, float, float], str] = COLOUR_MAP
) -> str | None:
    if not isinstance(colour, (list, tuple)) or len(colour) != 3:
        return None
    for expected, waste_type in colours.items():
        if all(
            abs(float(colour[index]) - expected[index]) <= _COLOUR_TOLERANCE
            for index in range(3)
        ):
            return waste_type
    return None


def _zone_centres(page: LTPage) -> list[tuple[float, float]]:
    """Return the horizontal centres of zone A and B for each month column."""
    from pdfminer.layout import LTChar, LTFigure

    columns: list[tuple[float, float]] = []
    for figure in page:
        if not isinstance(figure, LTFigure):
            continue
        chars = sorted(
            (
                element
                for element in _iter_elements(figure)
                if isinstance(element, LTChar) and element.get_text().strip()
            ),
            key=lambda element: element.x0,
        )
        if "".join(char.get_text() for char in chars).upper() != "ZONAAZONAB":
            continue
        zone_a = chars[:5]
        zone_b = chars[5:]
        columns.append(
            (
                (zone_a[0].x0 + zone_a[-1].x1) / 2,
                (zone_b[0].x0 + zone_b[-1].x1) / 2,
            )
        )
    return sorted(columns)


def _calendar_columns(
    page: LTPage, base_year: int
) -> list[tuple[int, int, list[tuple[int, float]], tuple[float, ...]]]:
    from pdfminer.layout import LTTextBoxHorizontal, LTTextLineHorizontal

    headings: list[tuple[float, int]] = []
    date_columns: list[tuple[float, float, list[tuple[int, float]]]] = []

    for element in page:
        if not isinstance(element, LTTextBoxHorizontal):
            continue

        text = " ".join(element.get_text().split())
        if month_match := _MONTH_RE.match(text):
            headings.append((element.x0, _MONTHS[month_match.group(1).casefold()]))

        days: list[tuple[int, float]] = []
        for line in element:
            if not isinstance(line, LTTextLineHorizontal):
                continue
            if day_match := _DAY_RE.fullmatch(" ".join(line.get_text().split())):
                days.append((int(day_match.group(1)), (line.y0 + line.y1) / 2))
        if len(days) >= 28:
            date_columns.append((element.x0, element.x1, days))

    headings.sort()
    date_columns.sort()
    zones: list[tuple[float, ...]] = list(_zone_centres(page))
    if not zones:
        # Single-zone layout: one symbol strip per month column.
        zones = [(x1 + _SINGLE_ZONE_OFFSET,) for _, x1, _ in date_columns]
    if not headings or not (len(headings) == len(date_columns) == len(zones)):
        raise ValueError(
            "Could not identify all month, date, and zone columns in the ETRA PDF. "
            "The PDF format may have changed."
        )

    result = []
    year = base_year
    previous_month: int | None = None
    for (_, month), (_, _, days), zone_centres in zip(
        headings, date_columns, zones, strict=True
    ):
        if previous_month is not None and month < previous_month:
            year += 1
        result.append((year, month, days, zone_centres))
        previous_month = month
    return result


def _parse_page(
    page: LTPage, base_year: int, zone_index: int
) -> list[tuple[date, str]]:
    from pdfminer.layout import LTCurve

    columns = _calendar_columns(page, base_year)
    zone_positions = [
        (column, index, centre)
        for column in columns
        for index, centre in enumerate(column[3])
    ]
    records: dict[tuple[date, str], tuple[date, str]] = {}

    for element in _iter_elements(page):
        if not isinstance(element, LTCurve) or not element.fill:
            continue
        waste_type = _waste_type(element.non_stroking_color)
        if waste_type is None:
            continue

        centre_x = (element.x0 + element.x1) / 2
        centre_y = (element.y0 + element.y1) / 2
        column, nearest_zone_index, zone_centre = min(
            zone_positions,
            key=lambda item: abs(item[2] - centre_x),
        )
        if (
            nearest_zone_index != zone_index
            or abs(zone_centre - centre_x) > _MAX_ZONE_DISTANCE
        ):
            continue

        day, day_y = min(column[2], key=lambda item: abs(item[1] - centre_y))
        if abs(day_y - centre_y) > _MAX_DAY_DISTANCE:
            continue

        collection_date = date(column[0], column[1], day)
        records[(collection_date, waste_type)] = (collection_date, waste_type)

    return list(records.values())


def _find_year(pages: list[LTPage]) -> int:
    from pdfminer.layout import LTTextBoxHorizontal

    for page in pages:
        for element in page:
            if not isinstance(element, LTTextBoxHorizontal):
                continue
            if year_match := _YEAR_RE.search(element.get_text()):
                return int(year_match.group(1))
    raise ValueError(
        "Could not determine the schedule year from the ETRA calendar PDF."
    )


class EtraCalendarParser(Parser["list[tuple[date, str]]"]):
    """Read one zone's collection dates from an ETRA-template calendar PDF.

    Consumes the PDF response from ``retrievers.PdfLinkRetriever`` and emits
    ``(date, label)`` records for an ``ICSTransformer``. ``zone_param`` names
    the ``source.params`` field holding the user's chosen zone ("A" or "B",
    case-insensitive). Pass ``zone_param=None`` for single-zone calendars,
    where ETRA publishes a separate PDF per zone and the page has no
    "ZONA A / ZONA B" sub-columns.
    """

    def __init__(self, *, zone_param: str | None = "zone"):
        self.zone_param = zone_param

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        from pdfminer.high_level import extract_pages

        zone_index = 0
        if self.zone_param is not None:
            zone_raw = source.params[self.zone_param] if source is not None else "A"
            zone = str(zone_raw).strip().upper()
            if zone not in ("A", "B"):
                raise SourceArgumentNotFoundWithSuggestions(
                    self.zone_param, zone_raw, ["A", "B"]
                )
            zone_index = 0 if zone == "A" else 1

        pages = list(extract_pages(BytesIO(response.content)))
        if not pages:
            raise ValueError("The ETRA calendar PDF contains no pages.")
        base_year = _find_year(pages)

        records: dict[tuple[date, str], tuple[date, str]] = {}
        for page in pages:
            for record in _parse_page(page, base_year, zone_index):
                records[record] = record
        return sorted(records.values())


# --- A5 booklet layout ("CALENDARIO_<Comune>gen_<year>.pdf") -----------------

# The booklet draws organic and garden waste in slightly different shades from
# the A4 grid (and the 2025 edition a brighter plastics yellow); the other
# symbols share the A4 colours.
BOOKLET_COLOUR_MAP: dict[tuple[float, float, float], str] = {
    **COLOUR_MAP,
    (0.469, 0.336, 0.291): "Umido organico",
    (0.884, 0.766, 0.603): "Verde e ramaglie",
    (1.0, 0.834, 0.0): "Plastica e metalli",
}
_GLASS_COLUMN = "VETRO"
_WEEKDAYS = ("LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM")
_BOOKLET_DAY_RE = re.compile(r"(\d{1,2})(" + "|".join(_WEEKDAYS) + r")")
_BOOKLET_YEAR_RE = re.compile(r"20\d\d")
# A zone column starts a little left of its heading text.
_COLUMN_MARGIN = 15
# A collection symbol is centred on its day's row; rows are ~31 pt apart.
_MAX_ROW_DISTANCE = 12
# The symbols are small; anything larger is an illustration.
_MAX_SYMBOL_SIZE = 25
# Glass markers are followed by an outlined "Zona N" label, drawn as black
# vector glyphs rather than text. The digit is the label's last glyph and is
# told apart by its outline's point count (ETRA's template font).
_GLASS_LABEL_REACH = 40
_GLASS_ZONE_GLYPHS = {8: "1", 30: "2", 50: "3", 16: "4"}
_LINE_TOLERANCE = 4
_WORD_GAP = 10


class _Line(NamedTuple):
    text: str
    x0: float
    x1: float
    y: float
    chars: tuple[LTChar, ...]


def _char_lines(chars: Iterable[LTChar]) -> list[_Line]:
    """Group loose glyphs (outlined headings) into lines of adjacent characters."""
    rows: list[list[LTChar]] = []
    for char in sorted(chars, key=lambda char: (char.y0 + char.y1) / 2):
        centre = (char.y0 + char.y1) / 2
        if (
            rows
            and abs((rows[-1][0].y0 + rows[-1][0].y1) / 2 - centre) <= _LINE_TOLERANCE
        ):
            rows[-1].append(char)
        else:
            rows.append([char])

    lines: list[_Line] = []
    for row in rows:
        row.sort(key=lambda char: char.x0)
        run: list[LTChar] = []
        for char in row:
            if run and char.x0 - run[-1].x1 > _WORD_GAP:
                lines.append(_line(run))
                run = []
            run.append(char)
        if run:
            lines.append(_line(run))
    return lines


def _line(chars: list[LTChar]) -> _Line:
    return _Line(
        text="".join(char.get_text() for char in chars),
        x0=chars[0].x0,
        x1=chars[-1].x1,
        y=sum((char.y0 + char.y1) / 2 for char in chars) / len(chars),
        chars=tuple(chars),
    )


def _page_lines(page: LTPage) -> tuple[list[_Line], list[_Line]]:
    """Return the page's text-layer lines and its outlined (figure) lines."""
    from pdfminer.layout import LTChar, LTFigure, LTTextLineHorizontal

    text_lines: list[_Line] = []
    for element in _iter_elements(page):
        if isinstance(element, LTTextLineHorizontal):
            chars = [
                char
                for char in element
                if isinstance(char, LTChar) and char.get_text().strip()
            ]
            if chars:
                text_lines.append(_line(chars))

    figure_chars = [
        char
        for figure in page
        if isinstance(figure, LTFigure)
        for char in _iter_elements(figure)
        if isinstance(char, LTChar) and char.get_text().strip()
    ]
    return text_lines, _char_lines(figure_chars)


def _column_starts(lines: list[_Line]) -> dict[str, float] | None:
    """Left edge of each column under a "ZONA A  ZONA B  VETRO" heading row."""
    for line in lines:
        if "ZONAA" not in line.text.upper():
            continue
        row = [other for other in lines if abs(other.y - line.y) <= _LINE_TOLERANCE]
        starts: dict[str, float] = {}
        for other in row:
            text = other.text.upper()
            for match in re.finditer(r"ZONA[A-Z]|" + _GLASS_COLUMN, text):
                label = match.group()
                if label.startswith("ZONA"):
                    label = f"ZONA {label[-1]}"
                starts[label] = other.chars[match.start()].x0 - _COLUMN_MARGIN
        return starts
    return None


def _glass_zone(symbol: LTCurve, curves: list[LTCurve], when: date) -> str:
    """Read the "Zona N" digit drawn to the right of a glass symbol."""
    centre = (symbol.y0 + symbol.y1) / 2
    label = sorted(
        (
            curve
            for curve in curves
            if _is_black(curve.non_stroking_color)
            and abs((curve.y0 + curve.y1) / 2 - centre) <= _MAX_DAY_DISTANCE
            and symbol.x1 <= curve.x0 <= symbol.x1 + _GLASS_LABEL_REACH
        ),
        key=lambda curve: curve.x0,
    )
    zone = _GLASS_ZONE_GLYPHS.get(len(label[-1].pts)) if label else None
    if zone is None:
        raise ValueError(
            f"Could not read the glass zone label for {when} in the ETRA booklet. "
            "The PDF format may have changed."
        )
    return zone


def _is_black(colour: Any) -> bool:
    if isinstance(colour, (int, float)):
        return float(colour) == 0
    return isinstance(colour, (list, tuple)) and all(float(c) == 0 for c in colour)


class _Month(NamedTuple):
    year: int
    month: int


def _booklet_page(
    page: LTPage,
    month: _Month | None,
    columns: dict[str, float] | None,
) -> tuple[
    _Month | None, dict[str, float] | None, list[tuple[date, str, str, str | None]]
]:
    """Read one booklet page; the month and columns carry over from the left page."""
    from pdfminer.layout import LTCurve

    text_lines, figure_lines = _page_lines(page)
    days = [
        (int(match.group(1)), match.group(2), line.y)
        for line in text_lines + figure_lines
        if (match := _BOOKLET_DAY_RE.fullmatch(line.text.upper()))
    ]
    if not days:
        return month, columns, []

    columns = _column_starts(figure_lines) or _column_starts(text_lines) or columns
    # A month heading in the text layer wins; an outlined heading (the next
    # year's January page) is the fallback.
    heading = next(
        (
            _MONTHS[line.text.casefold()]
            for lines in (text_lines, figure_lines)
            for line in lines
            if line.text.casefold() in _MONTHS
        ),
        None,
    )
    if heading is not None:
        year_line = next(
            (
                int(line.text)
                for line in figure_lines
                if _BOOKLET_YEAR_RE.fullmatch(line.text)
            ),
            None,
        )
        if year_line is not None:
            month = _Month(year_line, heading)
        elif month is not None:
            month = _Month(month.year + (heading < month.month), heading)
        else:
            raise ValueError("The ETRA booklet's first month has no year.")
    if month is None or month.month == 0 or not columns:
        raise ValueError(
            "Could not identify the month or zone columns in the ETRA booklet. "
            "The PDF format may have changed."
        )

    for day, weekday, _ in days:
        if _WEEKDAYS[date(month.year, month.month, day).weekday()] != weekday:
            raise ValueError(
                f"The ETRA booklet prints {day} {weekday} under "
                f"{month.month}/{month.year}; the PDF format may have changed."
            )

    curves = [
        element
        for element in _iter_elements(page)
        if isinstance(element, LTCurve) and element.fill
    ]
    by_left = sorted(columns.items(), key=lambda item: item[1])
    records: list[tuple[date, str, str, str | None]] = []
    for curve in curves:
        waste_type = _waste_type(curve.non_stroking_color, BOOKLET_COLOUR_MAP)
        if (
            waste_type is None
            or curve.width > _MAX_SYMBOL_SIZE
            or curve.height > _MAX_SYMBOL_SIZE
        ):
            continue
        centre_y = (curve.y0 + curve.y1) / 2
        day, _, row_y = min(days, key=lambda item: abs(item[2] - centre_y))
        if abs(row_y - centre_y) > _MAX_ROW_DISTANCE:
            continue
        column = next(
            (label for label, left in reversed(by_left) if curve.x0 >= left), None
        )
        if column is None:
            continue
        when = date(month.year, month.month, day)
        glass_zone = (
            _glass_zone(curve, curves, when) if column == _GLASS_COLUMN else None
        )
        records.append((when, column, waste_type, glass_zone))
    return month, columns, records


class EtraBookletParser(Parser["list[tuple[date, str]]"]):
    """Read one zone's collection dates from an ETRA A5 booklet calendar.

    ``zones`` maps each zone the user can choose to the booklet column it reads
    (``"ZONA A"`` / ``"ZONA B"``) and the glass sub-zone whose "Zona N" markers
    in the ``VETRO`` column apply to it (``None``: every glass marker).
    ``zone_param`` names the ``source.params`` field holding the chosen zone.
    Emits ``(date, label)`` records for an ``ICSTransformer``.
    """

    def __init__(
        self,
        *,
        zones: Mapping[str, tuple[str, str | None]],
        zone_param: str = "zone",
    ):
        self.zones = dict(zones)
        self.zone_param = zone_param

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        from pdfminer.high_level import extract_pages

        from waste_collection_schedule import lookups

        chosen = source.params[self.zone_param] if source is not None else None
        column, glass_zone = lookups.resolve(
            self.zones, chosen, argument=self.zone_param
        )

        pages = list(extract_pages(BytesIO(response.content)))
        if not pages:
            raise ValueError("The ETRA calendar PDF contains no pages.")
        month: _Month | None = _Month(_find_year(pages), 0)
        columns: dict[str, float] | None = None
        records: set[tuple[date, str]] = set()
        for page in pages:
            month, columns, found = _booklet_page(page, month, columns)
            for when, found_column, waste_type, found_glass in found:
                if found_column == column or (
                    found_column == _GLASS_COLUMN and glass_zone in (None, found_glass)
                ):
                    records.add((when, waste_type))
        return sorted(records)
