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

Currently used by one provider (San Martino di Lupari), but kept here rather
than in the source module because ETRA publishes the identical template --
same icon colours, same grid layout -- for every municipality in its
consortium; only the PDF URL and the municipality name differ.
"""

from __future__ import annotations

import re
from datetime import date
from io import BytesIO
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from pdfminer.layout import LTPage

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


def _iter_elements(container: Any) -> Any:
    from pdfminer.layout import LTContainer

    for element in container:
        yield element
        if isinstance(element, LTContainer):
            yield from _iter_elements(element)


def _waste_type(colour: Any) -> str | None:
    if not isinstance(colour, (list, tuple)) or len(colour) != 3:
        return None
    for expected, waste_type in COLOUR_MAP.items():
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
) -> list[tuple[int, int, list[tuple[int, float]], tuple[float, float]]]:
    from pdfminer.layout import LTTextBoxHorizontal, LTTextLineHorizontal

    headings: list[tuple[float, int]] = []
    date_columns: list[tuple[float, list[tuple[int, float]]]] = []

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
            date_columns.append((element.x0, days))

    headings.sort()
    date_columns.sort()
    zones = _zone_centres(page)
    if not headings or not (len(headings) == len(date_columns) == len(zones)):
        raise ValueError(
            "Could not identify all month, date, and zone columns in the ETRA PDF. "
            "The PDF format may have changed."
        )

    result = []
    year = base_year
    previous_month: int | None = None
    for (_, month), (_, days), zone_centres in zip(
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
    case-insensitive).
    """

    def __init__(self, *, zone_param: str = "zone"):
        self.zone_param = zone_param

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        from pdfminer.high_level import extract_pages

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
