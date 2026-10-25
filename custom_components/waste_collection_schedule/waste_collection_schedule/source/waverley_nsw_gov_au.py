"""Waverley Council (NSW), Australia.

The council's "Find your collection day" page loads a public CSV that maps
every address to a waste zone ("Zone B6", or "FOGO B9" where food organics
go in the green bin) and links one calendar PDF per zone; the zone-to-PDF
table is part of the page's script. Each PDF holds a season (July to June) as
twelve month grids. The bins are read from the colours of the day cells, as
the legend explains them: yellow container recycling, blue paper and
cardboard, green garden (or food and garden) organics, a cell split in two
colours for two bins. The bins' weekday heads its column in red (garbage,
collected every week); a tree icon marks the natural Christmas tree
collection, and an orange frame the Sunday evening to put out the scheduled
clean-up; the collection itself starts the Monday after ("commences on
MONDAY ..."), which is the date reported.

A cell's date comes from its place in the grid (month heading, weekday
column, week row) rather than from its printed day number, as the tree icon
replaces the number on its days. Every printed day number is checked against
its weekday column, so a changed layout fails loudly.
"""

import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, NamedTuple, final

from waste_collection_schedule import (
    parsers,
    recurrence,
    response_shape,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.PdfMarkerCalendar import to_rgb
from waste_collection_schedule.transformers import ICSTransformer

_SITE = "https://www.waverley.nsw.gov.au"
_PAGE = (
    f"{_SITE}/residents/waste_and_recycling/bins_and_collection_days/"
    "find_your_collection_day"
)
_CSV = f"{_SITE}/bin_collection_auto_suggestion_search/CollectionCombined2.csv"

_GARBAGE = "Garbage"
_RECYCLING = "Container Recycling"
_PAPER = "Paper and Cardboard"
_ORGANICS = "Garden Organics"
_FOGO = "Food and Garden Organics"
_TREE = "Natural Christmas Tree Collection"
_CLEAN_UP = "Scheduled Clean-Up"

# Legend colours (CMYK as the PDFs state them).
_RED = (0.0, 1.0, 0.71, 0.0)
_CELLS = {
    (0.0, 0.1, 1.0, 0.0): _RECYCLING,
    (1.0, 0.35, 0.0, 0.0): _PAPER,
    (0.5, 0.0, 1.0, 0.0): _ORGANICS,
}
_TREE_COLOR = (0.0, 0.0, 0.0, 1.0)
_FRAME_COLOR = (0.0, 0.58, 1.0, 0.05)

_HEADING_RE = re.compile(r"^([A-Za-z]+)\s+(20\d\d)$")
_DAY_RE = re.compile(r"^(?:[1-9]|[12]\d|3[01])$")
_POSTCODE_RE = re.compile(r"\s+nsw(?:\s+\d{4})?$")
_UNIT_RE = re.compile(r"^[^\s/]+/")


class _Month(NamedTuple):
    first: datetime.date
    top: float  # y of the weekday header row
    columns: tuple[float, ...]  # x of Sun..Sat


def _address_key(value: str) -> str:
    """Lower-case words, keeping unit slashes and number ranges, no state."""
    text = re.sub(r"[^\w/-]+", " ", str(value).casefold())
    return _POSTCODE_RE.sub("", " ".join(text.split()))


def _zone(response, address: str, **_) -> str:
    """The waste zone of the address; a building's units share one."""
    rows = parsers.CsvParser(require=["ADDRESS", "WasteZone"])(response)
    wanted = _address_key(address)
    zones = {
        row["WasteZone"].strip()
        for row in rows
        if _address_key(row["ADDRESS"]) == wanted
    }
    if not zones:
        zones = {
            row["WasteZone"].strip()
            for row in rows
            if _UNIT_RE.sub("", _address_key(row["ADDRESS"])) == wanted
        }
    if len(zones) == 1:
        return zones.pop()
    street = " ".join(w for w in wanted.split() if not any(c.isdigit() for c in w))
    raise SourceArgumentNotFoundWithSuggestions(
        "address",
        address,
        sorted(
            " ".join(row["ADDRESS"].split())
            for row in rows
            if street and street in _address_key(row["ADDRESS"])
        )[:50],
    )


def _calendar_url(response, zone: str, **_) -> str:
    """The zone's PDF, from the page script's ``case "<zone>": pdfLink = ...``."""
    match = re.search(
        rf'case\s+"{re.escape(zone)}"\s*:\s*pdfLink\s*=\s*"([^"]+)"', response.text
    )
    if match is None:
        raise ValueError(f"no calendar linked for waste zone {zone!r} on {_PAGE}")
    return match.group(1)


def _expect(condition: bool, detail: str, source: BaseSource) -> None:
    response_shape.expect(
        condition, source_name=response_shape.source_name(source), detail=detail
    )


def _is(color, wanted, tolerance: float = 0.08) -> bool:
    rgb, expected = to_rgb(color), to_rgb(wanted)
    return (
        rgb is not None
        and expected is not None
        and all(abs(a - b) <= tolerance for a, b in zip(rgb, expected, strict=True))
    )


def _months(layout: parsers.PdfWordLayout, source: BaseSource) -> list[_Month]:
    """The month grids: heading, weekday header row and its column positions."""
    headings = [
        (line, datetime.date(int(m[2]), month, 1))
        for line in layout.lines
        if line.page == 0
        and (m := _HEADING_RE.match(line.text))
        and (month := recurrence.month(m[1], "en")) is not None
    ]
    names = recurrence.weekday_names("en", abbreviated=True)
    header_words = sorted(
        (w for w in layout.words if w.page == 0 and w.text in names),
        key=lambda w: (round(-w.y), w.x),
    )
    months: list[_Month] = []
    # Header rows run Sun..Sat for each month side by side.
    rows: dict[int, list[parsers.PdfTextFragment]] = {}
    for word in header_words:
        rows.setdefault(round(word.y), []).append(word)
    for row in rows.values():
        row.sort(key=lambda w: w.x)
        for start in range(0, len(row) - 6, 7):
            group = row[start : start + 7]
            if [w.text for w in group] != [names[6], *names[:6]]:
                continue
            above = [
                (line, first)
                for line, first in headings
                if 0 < line.y - group[0].y < 25
                and group[0].x - 15 < line.x < group[-1].x
            ]
            if len(above) == 1:
                months.append(
                    _Month(above[0][1], group[0].y, tuple(w.x for w in group))
                )
    _expect(len(months) == 12, f"found {len(months)} month grids, not 12", source)
    return months


class _Grid:
    """Grid position -> date, with each month's week rows located by its
    printed day numbers (each checked against its weekday column)."""

    def __init__(self, layout: parsers.PdfWordLayout, source: BaseSource):
        self.months = _months(layout, source)
        self.rows: dict[_Month, dict[int, float]] = {m: {} for m in self.months}
        checked = 0
        for word in layout.words:
            if word.page != 0 or not _DAY_RE.match(word.text):
                continue
            place = self._place(word.x, word.y)
            if place is None:
                continue
            month, column = place
            lead = (month.first.weekday() + 1) % 7
            day = int(word.text)
            _expect(
                (day - 1 + lead) % 7 == column,
                f"{word.text} printed under the wrong weekday of {month.first:%B %Y}",
                source,
            )
            self.rows[month][(day - 1 + lead) // 7] = word.y
            checked += 1
        _expect(checked >= 300, f"only {checked} day numbers in the grids", source)

    def _place(self, x: float, y: float) -> "tuple[_Month, int] | None":
        for month in self.months:
            if not month.top - 75 < y < month.top - 4:
                continue
            column = min(range(7), key=lambda i: abs(month.columns[i] - x))
            if abs(month.columns[column] - x) < 6:
                return month, column
        return None

    def date(self, x: float, y: float) -> "datetime.date | None":
        place = self._place(x, y)
        if place is None:
            return None
        month, column = place
        rows = self.rows[month]
        row = min(rows, key=lambda r: abs(rows[r] - y), default=None)
        if row is None or abs(rows[row] - y) > 4:
            return None
        lead = (month.first.weekday() + 1) % 7
        day = month.first + datetime.timedelta(days=row * 7 + column - lead)
        return day if day.month == month.first.month else None

    def collection_weekdays(self, layout: parsers.PdfWordLayout) -> set[int]:
        """The weekday (0=Mon) of every column headed in red."""
        found = set()
        for v in layout.vectors:
            if v.page != 0 or not _is(v.fill_color, _RED):
                continue
            x, y = (v.x0 + v.x1) / 2, (v.y0 + v.y1) / 2
            for month in self.months:
                if abs(month.top - y) < 3:
                    column = min(range(7), key=lambda i: abs(month.columns[i] - x))
                    if abs(month.columns[column] - x) < 6:
                        found.add((column - 1) % 7)
        return found


def _collections(
    layouts: list[parsers.PdfWordLayout], source: BaseSource
) -> Iterable[tuple[datetime.date, str]]:
    layout = layouts[0]
    grid = _Grid(layout, source)

    weekdays = grid.collection_weekdays(layout)
    _expect(len(weekdays) == 1, f"collection weekday unclear ({weekdays})", source)
    weekday = weekdays.pop()
    for month in grid.months:
        day = recurrence.next_weekday(weekday, on_or_after=month.first)
        while day.month == month.first.month:
            yield day, _GARBAGE
            day += datetime.timedelta(days=7)

    # A FOGO zone's legend: "Green Lid - Food Organics and Garden Organics".
    fogo = any("Food Organics" in line.text for line in layout.lines)
    found: set[tuple[datetime.date, str]] = set()
    for v in layout.vectors:
        if v.page != 0:
            continue
        width, height = v.x1 - v.x0, v.y1 - v.y0
        if v.fill_color is not None and 12 <= width <= 20 and 6 <= height <= 13:
            label = next((t for c, t in _CELLS.items() if _is(v.fill_color, c)), None)
        elif v.fill_color is not None and 6 <= width <= 11 and 6 <= height <= 11:
            label = _TREE if _is(v.fill_color, _TREE_COLOR) else None
        elif v.fill_color is None and 12 <= width <= 20 and 6 <= height <= 16:
            label = _CLEAN_UP if _is(v.stroke_color, _FRAME_COLOR) else None
        else:
            label = None
        if label == _ORGANICS and fogo:
            label = _FOGO
        if label and (day := grid.date((v.x0 + v.x1) / 2, (v.y0 + v.y1) / 2)):
            if label == _CLEAN_UP:
                # The frame marks the put-out evening; collection is next day.
                day += datetime.timedelta(days=1)
            found.add((day, label))
    bins = sum(1 for _d, label in found if label in (_RECYCLING, _PAPER))
    _expect(bins >= 40, f"only {bins} recycling or paper days found", source)
    yield from sorted(found)


@final
class Source(BaseSource):
    TITLE = "Waverley Council"
    DESCRIPTION = "Source for Waverley Council (NSW) kerbside collection."
    URL = "https://www.waverley.nsw.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.ORGANIC,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "585 Old South Head Road, Rose Bay": {
            "address": "585 Old South Head Road, Rose Bay NSW 2029"
        },
        "FOGO zone: 423 Old South Head Road, Rose Bay": {
            "address": "423 Old South Head Road ROSE BAY NSW 2029"
        },
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your address as the council's 'Find your collection day' "
            "search lists it, e.g. '1 Aboukir Street Dover Heights' or a unit "
            "as '2/585 Old South Head Road Rose Bay' (state and postcode are "
            "optional). A whole building's address works when all its units "
            "share one waste zone."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(_CSV, pick=_zone, timeout=60),
            retrievers.Lookup(_PAGE, pick=_calendar_url),
        ),
        url=lambda _zone, pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = parsers.PdfWordLayoutParser(
        min_words=300, include_form_text=True, include_strokes=True
    )
    preprocess = staticmethod(_collections)
    transform = ICSTransformer(
        type_value_map={
            _GARBAGE: wt.GENERAL_WASTE,
            _RECYCLING: wt.RECYCLABLES,
            _PAPER: wt.PAPER,
            _ORGANICS: wt.GARDEN_WASTE,
            _FOGO: wt.ORGANIC,
            _TREE: wt.GARDEN_WASTE,
            _CLEAN_UP: wt.BULKY_WASTE,
        }
    )
