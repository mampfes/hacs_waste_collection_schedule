"""Waste collection schedules for Noble Environmental (Pennsylvania, US).

Noble Environmental publishes one colour-coded yearly calendar PDF per
municipality it serves. The PDFs are listed in the site's public WordPress
media library, so the configured municipality is resolved there to the newest
calendar for the current year.

Each PDF is a grid of twelve month blocks. A day is a collection day when its
cell is filled with one of the colours explained in the PDF's own legend, so
the legend is read from every PDF rather than hard-coded. Day numbers of the
neighbouring months (the leading days of the previous month and the trailing
days of the next one, e.g. January of the following year after December) are
ignored, and each month's year is derived from the weekday its 1st falls on,
which also covers the calendars that span two years.

Holidays: the calendars already print the shifted collection days ("If Holiday
falls on a weekday, collection is pushed back one day for all days that
follow"), so the dates are taken as printed and the holiday cells themselves
are not emitted as collections.
"""

import calendar
import html
import re
from collections.abc import Iterable, Sequence
from datetime import date
from typing import Any, ClassVar, final

from waste_collection_schedule import parsers, preprocessors, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import ICSTransformer

_MEDIA_URL = "https://nobleenviro.com/wp-json/wp/v2/media"

_GARBAGE_RECYCLING = [wt.GENERAL_WASTE, wt.RECYCLABLES]
_GARBAGE_YARD = [wt.GENERAL_WASTE, wt.GARDEN_WASTE]

# Legend labels as printed in the 2026 calendars. Holidays and the drop-off
# events some municipalities print are not curbside collections.
_TYPE_MAP: dict[str, Any] = {
    "Garbage Collection Only": wt.GENERAL_WASTE,
    "Garbage Collection": wt.GENERAL_WASTE,
    "Recycle/Garbage Collection": _GARBAGE_RECYCLING,
    "Garbage and Recycling Collection": _GARBAGE_RECYCLING,
    "North Union Recycle/Garbage": _GARBAGE_RECYCLING,
    "South Union Recycle/Garbage": _GARBAGE_RECYCLING,
    "Recycle Collection": wt.RECYCLABLES,
    "Recycle/Yard Waste": [wt.RECYCLABLES, wt.GARDEN_WASTE],
    "Recycle/Yard Waste Collection": [wt.RECYCLABLES, wt.GARDEN_WASTE],
    "Yard Waste Collection": wt.GARDEN_WASTE,
    "Leaf/Yard Waste Collection": wt.GARDEN_WASTE,
    "Curbside Leaf Collection": wt.GARDEN_WASTE,
    "Wood Waste Collection": wt.GARDEN_WASTE,
    "Yard Waste/Garbage": _GARBAGE_YARD,
    "Garbage/Yard Waste Collection": _GARBAGE_YARD,
    "Leaf/Yard Waste/Garbage": _GARBAGE_YARD,
    "Bulk Item/Garbage": [wt.GENERAL_WASTE, wt.BULKY_WASTE],
    "Garbage/Bulk Collection": [wt.GENERAL_WASTE, wt.BULKY_WASTE],
    "E-Waste Collection": wt.ELECTRONICS,
    "Holiday": None,
    "Observed Holiday": None,
    "Household Hazardous Waste": None,
    "Paper Shredding Events": None,
    "Electronics Recycling Events": None,
}

_MONTHS = {name: number for number, name in enumerate(calendar.month_name) if name}
_WEEKDAYS = ("Su", "Mo", "Tu", "We", "Th", "Fr", "Sa")
# date.weekday() of each column, the calendars start their weeks on Sunday.
_COLUMN_WEEKDAY = (6, 0, 1, 2, 3, 4, 5)
_DAY_RE = re.compile(r"^\d{1,2}$")
_YEAR_RE = re.compile(r"20\d\d")
_MAX_CELL = 40.0
_MAX_BLOCK_WIDTH = 140.0
_MAX_BLOCK_HEIGHT = 110.0
_COLOUR_TOLERANCE = 0.5


def _normalise(value: str) -> str:
    return " ".join(value.split()).casefold()


def _municipality_name(title: str) -> str:
    """'Connellsville &#8211; 2025 &#8211; 2026' -> 'Connellsville'."""
    name = html.unescape(title)
    name = re.split(r"\s*[-\u2013]?\s*20\d\d", name, maxsplit=1)[0]
    return name.strip(" -\u2013")


def _calendar_url(response, *_, municipality: str, **__) -> str:
    """Pick the newest calendar PDF of the configured municipality."""
    items = response.json()
    response_shape.expect(
        isinstance(items, list),
        source_name="Noble Environmental",
        detail="media search did not return a list",
        raw=response.text[:500],
    )
    wanted = _normalise(municipality)
    candidates: list[tuple[int, str, str]] = []
    names: set[str] = set()
    for item in items:
        title = str((item.get("title") or {}).get("rendered", ""))
        url = str(item.get("source_url", ""))
        if not url.lower().endswith(".pdf") or not _YEAR_RE.search(title):
            continue
        name = _municipality_name(title)
        names.add(name)
        if _normalise(name) != wanted:
            continue
        years = [int(year) for year in _YEAR_RE.findall(title)]
        candidates.append((max(years), str(item.get("date", "")), url))
    if not candidates:
        raise SourceArgumentNotFoundWithSuggestions(
            "municipality", municipality, sorted(names)
        )
    this_year = date.today().year
    current = [c for c in candidates if c[0] >= this_year]
    if current:
        # The calendar for this year (or the one reaching into it), newest upload.
        best_year = min(c[0] for c in current)
        pool = [c for c in current if c[0] == best_year]
    else:
        best_year = max(c[0] for c in candidates)
        pool = [c for c in candidates if c[0] == best_year]
    return max(pool, key=lambda c: c[1])[2]


def _colour_key(colour: Sequence[float] | None) -> tuple[float, ...] | None:
    if not colour:
        return None
    return tuple(round(float(value), 3) for value in colour)


def _colour_distance(first: tuple[float, ...], second: tuple[float, ...]) -> float:
    if len(first) != len(second):
        return float("inf")
    return sum((a - b) ** 2 for a, b in zip(first, second, strict=True)) ** 0.5


def _is_neutral(colour: tuple[float, ...]) -> bool:
    """White, black and the greys used for weekends and headers."""
    return len(colour) == 1 or max(colour) - min(colour) < 0.05


def _cells(layout: parsers.PdfDocumentLayout) -> list[parsers.PdfVector]:
    """Filled rectangles inside a month block, smallest first.

    A collection day is usually a single cell, but adjacent cells of one
    colour are often drawn as one rectangle: across a row where a municipality
    is served on several days of a week (one area per day), down a column for
    consecutive weeks. Legend swatches are cell-sized too.
    """
    return sorted(
        (
            vector
            for vector in layout.vectors
            if vector.fill_color
            and 3 < vector.x1 - vector.x0 < _MAX_BLOCK_WIDTH
            and 3 < vector.y1 - vector.y0 < _MAX_BLOCK_HEIGHT
        ),
        key=lambda vector: (vector.x1 - vector.x0) * (vector.y1 - vector.y0),
    )


def _legend(
    layout: parsers.PdfDocumentLayout, cells: list[parsers.PdfVector]
) -> list[tuple[tuple[float, ...], str]]:
    """Read the legend: a swatch directly left of its label."""
    legend: list[tuple[tuple[float, ...], str]] = []
    for fragment in layout.fragments:
        text = " ".join(fragment.text.split()).strip(" -*")
        if (
            not text
            or _DAY_RE.fullmatch(text)
            or text in _MONTHS
            or text in _WEEKDAYS
            or not any(ch.isalpha() for ch in text)
        ):
            continue
        for vector in cells:
            if (
                vector.x1 - vector.x0 < _MAX_CELL
                and vector.page == fragment.page
                and fragment.x - 8 <= vector.x1 <= fragment.x + 1
                and vector.y0 - 4 <= fragment.y <= vector.y1
            ):
                colour = _colour_key(vector.fill_color)
                if colour is not None:
                    legend.append((colour, text))
                break
    return legend


def _label_for(
    colour: tuple[float, ...] | None, legend: list[tuple[tuple[float, ...], str]]
) -> str | None:
    """The legend label of a cell colour.

    Some calendars fill their cells with a slightly different shade than the
    legend swatch (e.g. a darker purple), so the nearest legend colour wins
    within a tolerance. Neutral fills (white, weekend greys) are never a
    collection.
    """
    if colour is None or _is_neutral(colour):
        return None
    distances = sorted((_colour_distance(key, colour), label) for key, label in legend)
    if not distances or distances[0][0] > _COLOUR_TOLERANCE:
        return None
    labels = {label for distance, label in distances if distance == distances[0][0]}
    # A colour the legend uses twice (e.g. holiday and leaf collection both
    # red) cannot be told apart, so it is skipped rather than guessed.
    return labels.pop() if len(labels) == 1 else None


def _weekday_rows(
    weekdays: list[parsers.PdfTextFragment],
) -> list[list[parsers.PdfTextFragment]]:
    """Split the weekday headings into runs of Su .. Sa, one per month block."""
    ordered = sorted(weekdays, key=lambda f: (f.page, -round(f.y), f.x))
    rows: list[list[parsers.PdfTextFragment]] = []
    for index in range(len(ordered) - 6):
        run = ordered[index : index + 7]
        if tuple(f.text.strip() for f in run) == _WEEKDAYS and all(
            f.page == run[0].page and round(f.y) == round(run[0].y) for f in run
        ):
            rows.append(run)
    return rows


def _block_year(
    month: int, first_column: int, candidate_years: Iterable[int]
) -> int | None:
    matches = [
        year
        for year in candidate_years
        if date(year, month, 1).weekday() == _COLUMN_WEEKDAY[first_column]
    ]
    return matches[0] if len(matches) == 1 else None


def _calendar_rows(
    records: parsers.PdfDocumentLayout, source: BaseSource | None = None
) -> Iterable[tuple[date, str]]:
    """Read every coloured day cell of the twelve month blocks."""
    layout = records
    source_name = response_shape.source_name(source)
    headers = [f for f in layout.fragments if f.text.strip() in _MONTHS]
    weekdays = [f for f in layout.fragments if f.text.strip() in _WEEKDAYS]
    response_shape.expect(
        len(headers) >= 6 and len(weekdays) >= 7 * len(headers),
        source_name=source_name,
        detail=(
            "no month blocks found in the calendar PDF; this municipality's "
            "calendar layout is not supported"
        ),
        raw=layout.text[:500],
    )
    weeks = _weekday_rows(weekdays)
    cells = _cells(layout)
    legend = _legend(layout, cells)
    response_shape.expect(
        bool(legend),
        source_name=source_name,
        detail="no colour legend found in the calendar PDF",
        raw=layout.text[:500],
    )

    years = {int(year) for year in _YEAR_RE.findall(layout.text)}
    response_shape.expect(
        bool(years),
        source_name=source_name,
        detail="no year found in the calendar PDF",
        raw=layout.text[:500],
    )
    candidate_years = sorted({year + delta for year in years for delta in (-1, 0, 1)})

    for header in headers:
        month = _MONTHS[header.text.strip()]
        # The weekday row (Su .. Sa) directly below the month name.
        row = next(
            (
                week
                for week in weeks
                if week[0].page == header.page
                and week[0].y < header.y < week[0].y + 30
                and week[0].x - 20 < header.x < week[-1].x + 20
            ),
            None,
        )
        if row is None:
            continue
        columns = [f.x for f in row]
        row_y = row[0].y
        left, right = columns[0] - 8, columns[-1] + 20
        # The next month block below this one bounds its day numbers.
        below = [
            h.y
            for h in headers
            if h.page == header.page and h.y < row_y and left - 20 < h.x < right
        ]
        floor = max(below) if below else float("-inf")
        days = sorted(
            (
                f
                for f in layout.fragments
                if f.page == header.page
                and _DAY_RE.fullmatch(f.text.strip())
                and left <= f.x <= right
                and floor < f.y < row_y
            ),
            key=lambda f: (-round(f.y), f.x),
        )
        # Keep only the run 1, 2, 3, ... of this month: drops the leading
        # days of the previous month and the trailing days of the next one.
        sequence: list[parsers.PdfTextFragment] = []
        for fragment in days:
            if int(fragment.text) == len(sequence) + 1:
                sequence.append(fragment)
        if not sequence:
            continue
        first_column = min(
            range(7), key=lambda index: abs(columns[index] - sequence[0].x)
        )
        year = _block_year(month, first_column, candidate_years)
        response_shape.expect(
            year is not None,
            source_name=source_name,
            detail=f"could not determine the year of {header.text.strip()}",
            raw=layout.text[:500],
        )
        assert year is not None
        last_day = calendar.monthrange(year, month)[1]
        for fragment in sequence[:last_day]:
            cx, cy = fragment.x + 2, fragment.y + 2
            cell = next(
                (
                    vector
                    for vector in cells
                    if vector.page == fragment.page
                    and vector.x0 <= cx <= vector.x1
                    and vector.y0 <= cy <= vector.y1
                ),
                None,
            )
            label = _label_for(_colour_key(cell.fill_color) if cell else None, legend)
            if label is not None:
                yield date(year, month, int(fragment.text)), label


@final
class Source(BaseSource):
    TITLE = "Noble Environmental"
    DESCRIPTION = (
        "Source for Noble Environmental (formerly County Hauling), Pennsylvania, US."
    )
    URL = "https://nobleenviro.com/"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.ELECTRONICS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Canonsburg": {"municipality": "Canonsburg"},
        "Verona": {"municipality": "Verona"},
        "Springdale Borough": {"municipality": "Springdale Borough"},
        "Connellsville (2025-2026 calendar)": {"municipality": "Connellsville"},
    }

    PARAMS = (municipality(),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your municipality exactly as Noble Environmental names its "
            "calendar PDF (e.g. 'Canonsburg' or 'Springdale Borough'). Enter any "
            "value once to get the list of available municipalities. Holiday "
            "shifts are taken from the calendar as printed."
        ),
        "de": (
            "Gib deine Gemeinde so ein, wie Noble Environmental ihren "
            "Kalender-PDF benennt (z. B. 'Canonsburg' oder 'Springdale Borough'). "
            "Gib einmal einen beliebigen Wert ein, um die Liste der verfügbaren "
            "Gemeinden zu erhalten. Feiertagsverschiebungen werden wie im "
            "Kalender gedruckt übernommen."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _MEDIA_URL,
                params=lambda municipality, **_: {
                    "search": municipality,
                    "mime_type": "application/pdf",
                    "per_page": 100,
                },
                raise_for_status=True,
                pick=_calendar_url,
            ),
        ),
        url=lambda calendar_url, **_: calendar_url,
        raise_for_status=True,
        timeout=60,
    )
    parse = parsers.PdfLayoutParser(min_fragments=100, min_vectors=50)
    preprocess = preprocessors.Compose(
        _calendar_rows,
        preprocessors.Deduplicate(),
        preprocessors.SortRows(),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP, carry_raw_label=True)
