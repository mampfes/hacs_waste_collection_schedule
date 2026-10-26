"""Pipeline components for printed PDF calendars with coloured marker symbols.

Many municipalities (most of them French) publish a yearly PDF calendar whose
day numbers are text while the collections are small coloured *vector* symbols:
a yellow dot beside the day for packaging, a grey square for household waste,
or a coloured disc or box painted behind the day number. Two layouts occur:

* **day rows**: one column per month, one row per day (``1 J``, ``2 V``, ...),
  the symbols to the right of the day number;
* **month grids**: one mini calendar (weeks x weekdays) per month, the symbol a
  filled shape behind the day number.

:class:`MarkerCalendarParser` reads either from a
:class:`~waste_collection_schedule.parsers.PdfWordLayoutParser` layout. A
:class:`Marker` describes one legend entry by its fill colour and size; every
matching vector is bound to the day number it belongs to, and the day number to
its month. Months come from the printed month headings when there are any, and
otherwise from the order of the day-row columns (a calendar whose headings are
outlined artwork rather than text). The parser yields ``(date, label)`` rows for
an ``ICSTransformer``.

A printed weekday initial beside the day number (``weekdays="LMMJVSD"``) is
checked against the computed date, so a misread layout fails loudly instead of
shifting the schedule.
"""

from __future__ import annotations

import datetime
import itertools
import re
import unicodedata
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, NamedTuple

from waste_collection_schedule import recurrence, response_shape
from waste_collection_schedule.parsers import (
    Parser,
    PdfTextFragment,
    PdfVector,
    PdfWordLayoutParser,
)

if TYPE_CHECKING:
    from curl_cffi.requests import Response

    from waste_collection_schedule.base_source import BaseSource

_DAY_RE = re.compile(r"^(?:[1-9]|[12]\d|3[01])$")
_YEAR_RE = re.compile(r"(?<!\d)(20\d{2})(?!\d)")


class Marker(NamedTuple):
    """One legend entry: the fill colour and size of its symbol.

    ``color`` is the fill as the PDF states it, an RGB triple, a CMYK
    quadruple or a single grey (all 0..1); both sides are converted to RGB
    before comparing. ``tolerance`` is the largest difference allowed
    per channel. ``width`` and ``height`` bound the symbol's size in points, which
    tells a small marker from a row or cell shading of a similar colour.

    ``frame`` makes the symbol a cell *outline* (a second collection drawn as a
    coloured border around a filled day cell): a day number is marked when bars
    of the colour, their thinner side within ``frame`` (points), border it on
    all four sides, ``width`` and ``height`` bounding the outlined cell.
    """

    label: str
    color: tuple[float, ...]
    tolerance: float = 0.08
    width: tuple[float, float] = (3.0, 20.0)
    height: tuple[float, float] = (3.0, 20.0)
    frame: tuple[float, float] | None = None


class _Anchor(NamedTuple):
    page: int
    day: int
    x: float
    y: float


def to_rgb(color: Sequence[float] | None) -> tuple[float, float, float] | None:
    """An RGB triple for a greyscale, RGB or CMYK colour, or None."""
    if not color:
        return None
    values = [float(value) for value in color]
    if len(values) == 1:
        return (values[0], values[0], values[0])
    if len(values) == 3:
        return (values[0], values[1], values[2])
    if len(values) == 4:
        c, m, y, k = values
        return ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
    return None


def _same_color(vector: PdfVector, marker: Marker) -> bool:
    rgb = to_rgb(vector.fill_color)
    expected = to_rgb(marker.color)
    return (
        rgb is not None
        and expected is not None
        and all(
            abs(value - wanted) <= marker.tolerance
            for value, wanted in zip(rgb, expected, strict=True)
        )
    )


def _framed(
    vectors: Sequence[PdfVector], marker: Marker, anchors: Sequence[_Anchor]
) -> list[_Anchor]:
    """The day numbers a frame ``marker`` outlines on all four sides."""
    assert marker.frame is not None
    thin_min, thin_max = marker.frame
    bars = [
        v
        for v in vectors
        if thin_min <= min(v.x1 - v.x0, v.y1 - v.y0) <= thin_max
        and _same_color(v, marker)
    ]

    def beside(offset: float, size: tuple[float, float]) -> bool:
        return size[0] / 2 - thin_max <= offset <= size[1] / 2 + thin_max

    framed = []
    for a in anchors:
        sides = set()
        for bar in bars:
            if bar.page != a.page:
                continue
            if bar.y1 - bar.y0 > bar.x1 - bar.x0 and bar.y0 <= a.y <= bar.y1:
                offset = (bar.x0 + bar.x1) / 2 - a.x
                if beside(abs(offset), marker.width):
                    sides.add("right" if offset > 0 else "left")
            elif bar.x0 <= a.x <= bar.x1:
                offset = (bar.y0 + bar.y1) / 2 - a.y
                if beside(abs(offset), marker.height):
                    sides.add("top" if offset > 0 else "bottom")
        if len(sides) == 4:
            framed.append(a)
    return framed


def _fold(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )


def _month_of(text: str) -> int | None:
    word = re.sub(r"[^a-z]", "", _fold(text).lower())
    if len(word) < 3:
        return None
    month = recurrence.month(word)
    if month is None:
        month = recurrence.month(text.strip().lower())
    return month


class MarkerCalendarParser(Parser["list[tuple[datetime.date, str]]"]):
    """Read a PDF calendar whose collections are coloured vector symbols.

    Args:
        markers: the legend, one :class:`Marker` per symbol.
        placement: ``"row"`` for symbols printed right of the day number (a day
            per row), ``"cell"`` for a symbol painted behind the day number (a
            month grid).
        first_month: the month of the first column or heading (a calendar
            running from April to March passes 4); later months that wrap past
            December belong to the following year. ``None`` takes it from the
            first month heading on the page (a season calendar whose start
            month may move).
        year_pattern: a regex whose first group is the calendar's (first) year,
            searched in the PDF text and then in the response URL. Without a
            match the earliest ``20xx`` in either is used. A year printed in
            two pieces ("20" stacked over "26") is matched with one group per
            piece, the groups joined: ``r"Giugno\\s+(20)\\s+(\\d\\d)\\b"``.
        weekdays: the weekday names printed beside each day number (or, in a
            month grid, at the head of its column), Monday first: a string of
            initials (``"LMMJVSD"``) or a sequence of abbreviations (``("LU",
            "MA", "ME", "JE", "VE", "SA", "DI")``); a mismatch fails loudly,
            and they settle the year when the PDF names another.
        row_reach: for ``placement="row"``, how far (points) right of its day
            number a symbol may sit.
        pages: zero-based page numbers to read; all pages when unset. Or a
            ``callable(**source.params) -> page numbers`` for a PDF holding one
            calendar per page, chosen by a param.
        read_headings: bind day numbers to the printed month headings (the
            default). ``False`` numbers the day-row columns in reading order
            from ``first_month`` instead, for a calendar whose headings sit too
            unevenly over their columns to be told from prose.
        include_form_text: also read text drawn inside Form XObjects (see
            ``PdfWordLayoutParser``), for a PDF whose day numbers are there.
        min_markers: fewest symbols expected; fewer raise
            ``ResponseShapeError`` (a changed design or an image-only PDF).
    """

    def __init__(
        self,
        markers: Sequence[Marker],
        *,
        placement: str = "row",
        first_month: int | None = 1,
        year_pattern: str | None = None,
        weekdays: str | Sequence[str] | None = None,
        row_reach: float = 60.0,
        pages: Sequence[int] | Callable[..., Sequence[int]] | None = None,
        min_markers: int = 10,
        include_form_text: bool = False,
        read_headings: bool = True,
    ):
        if placement not in ("row", "cell"):
            raise ValueError("placement must be 'row' or 'cell'")
        self.markers = tuple(markers)
        self.placement = placement
        self.first_month = first_month
        self.year_re = re.compile(year_pattern, re.IGNORECASE) if year_pattern else None
        self.weekdays = tuple(name.upper() for name in weekdays) if weekdays else None
        self.row_reach = row_reach
        self.pages = pages
        self.min_markers = min_markers
        self.include_form_text = include_form_text
        self.read_headings = read_headings

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[tuple[datetime.date, str]]:
        layout = PdfWordLayoutParser(
            min_words=28, include_form_text=self.include_form_text
        )(response, source)[0]
        name = response_shape.source_name(source)
        url = str(getattr(response, "url", "") or "")
        year = self._year(" ".join(line.text for line in layout.lines), url)
        response_shape.expect(
            year is not None,
            source_name=name,
            detail="no calendar year in the PDF or its URL",
            raw=url,
        )
        if year is None:
            return []

        pages = self.pages
        if callable(pages):
            pages = pages(**(source.params if source else {}))
        wanted = set(pages) if pages is not None else None
        words = [w for w in layout.words if wanted is None or w.page in wanted]
        anchors = [
            _Anchor(w.page, int(w.text), w.x, w.y)
            for w in words
            if _DAY_RE.match(w.text)
        ]
        months, first_heading = (
            self._months_from_headings(words, anchors)
            if self.read_headings
            else ({}, None)
        )
        if not months:
            months = self._months_from_columns(anchors)
        first_month = self.first_month or first_heading or 1
        response_shape.expect(
            bool(months),
            source_name=name,
            detail="no month headings or day columns found",
            raw=str(layout.lines[:20]),
        )

        vectors = [v for v in layout.vectors if wanted is None or v.page in wanted]
        hits = [
            (anchor, marker)
            for vector in vectors
            if (marker := self._marker(vector)) is not None
            for anchor in self._anchors_of(vector, anchors)
        ]
        hits.extend(
            (anchor, marker)
            for marker in self.markers
            if marker.frame is not None
            for anchor in _framed(vectors, marker, anchors)
        )

        marked: list[tuple[_Anchor, int, str, str | None]] = []
        for anchor, marker in hits:
            if anchor not in months:
                continue
            initial = self._initial(anchor, words) if self.weekdays else None
            marked.append((anchor, months[anchor], marker.label, initial))

        response_shape.expect(
            len(marked) >= self.min_markers,
            source_name=name,
            detail=(
                f"found {len(marked)} collection symbols, expected {self.min_markers}+"
            ),
            raw=str(layout.lines[:20]),
        )
        if self.weekdays:
            # A calendar reissued under last year's file name: the printed
            # weekdays tell which year the grid really is.
            year = min(
                (year, year + 1, year - 1),
                key=lambda candidate: self._dated(marked, candidate, first_month)[2],
            )
        rows, checked, mismatched = self._dated(marked, year, first_month)
        response_shape.expect(
            mismatched <= checked // 10,
            source_name=name,
            detail=(
                f"{mismatched} of {checked} marked days fall on another weekday "
                "than printed (layout changed?)"
            ),
        )
        return sorted(rows)

    def _dated(
        self,
        marked: list[tuple[_Anchor, int, str, str | None]],
        year: int,
        first_month: int,
    ) -> tuple[set[tuple[datetime.date, str]], int, int]:
        """The dated rows for ``year``, and how many printed weekdays disagree."""
        rows: set[tuple[datetime.date, str]] = set()
        checked = mismatched = 0
        for anchor, month, label, initial in marked:
            try:
                day = datetime.date(
                    year + (1 if month < first_month else 0), month, anchor.day
                )
            except ValueError:
                continue
            if self.weekdays and initial is not None:
                checked += 1
                weekday = day.weekday()
                # A grid of working days prints five names only.
                expected = (
                    self.weekdays[weekday] if weekday < len(self.weekdays) else None
                )
                if initial != expected:
                    mismatched += 1
                    continue
            rows.add((day, label))
        return rows, checked, mismatched

    def _year(self, text: str, url: str) -> int | None:
        for haystack in (text, url):
            if self.year_re and (match := self.year_re.search(haystack)):
                return int("".join(group for group in match.groups() if group))
        for haystack in (text, url):
            years = [int(y) for y in _YEAR_RE.findall(haystack)]
            if years:
                return min(years)
        return None

    def _marker(self, vector: PdfVector) -> Marker | None:
        width = vector.x1 - vector.x0
        height = vector.y1 - vector.y0
        for marker in self.markers:
            if (
                marker.frame is None
                and marker.width[0] <= width <= marker.width[1]
                and marker.height[0] <= height <= marker.height[1]
                and _same_color(vector, marker)
            ):
                return marker
        return None

    def _anchors_of(self, vector: PdfVector, anchors: list[_Anchor]) -> list[_Anchor]:
        """The day numbers a symbol marks: one, or a run of them."""
        if self.placement == "cell":
            width = vector.x1 - vector.x0
            height = vector.y1 - vector.y0
            if max(width, height) > 2 * min(width, height):
                # A bar painted over the same weekday of several weeks (or
                # several days of one week) marks every day number inside it.
                # A half-cell fill can end just above the text's centre;
                # tolerate that offset without reaching a neighbouring row.
                return [
                    a
                    for a in anchors
                    if a.page == vector.page
                    and vector.x0 - 2 <= a.x <= vector.x1 + 2
                    and vector.y0 - 2 <= a.y <= vector.y1 + 2
                ]
            # The symbol is painted behind its day number; a small one partly
            # hidden behind another symbol may no longer cover the number, so
            # allow a few points around it. A day cell's own fill needs none
            # (and an empty cell must not reach the day below it).
            slack = max(width, height) / 2 if max(width, height) < 16 else 1.0
            inside = [
                a
                for a in anchors
                if a.page == vector.page
                and vector.x0 - slack <= a.x <= vector.x1 + slack
                and vector.y0 - slack <= a.y <= vector.y1 + slack
            ]
            centre_x = (vector.x0 + vector.x1) / 2
            centre_y = (vector.y0 + vector.y1) / 2
            nearest = min(
                inside,
                key=lambda a: abs(a.x - centre_x) + abs(a.y - centre_y),
                default=None,
            )
            return [nearest] if nearest else []
        left = [
            a
            for a in anchors
            if a.page == vector.page
            and vector.y0 - 3 <= a.y <= vector.y1 + 3
            and vector.x0 - self.row_reach <= a.x <= vector.x0 + 2
        ]
        if not left:
            return []
        # The window can reach a neighbouring row: keep the row level with the
        # symbol, then the nearest day number left of it.
        centre_y = (vector.y0 + vector.y1) / 2
        level = min(abs(a.y - centre_y) for a in left)
        return [
            max(
                (a for a in left if abs(a.y - centre_y) <= level + 1.5),
                key=lambda a: a.x,
            )
        ]

    def _initial(self, anchor: _Anchor, words: list[PdfTextFragment]) -> str | None:
        """The weekday name printed level with a day number or, in a month
        grid, at the head of its column."""
        names = set(self.weekdays or ())

        def name(word: PdfTextFragment) -> str:
            return word.text.upper().rstrip(".")

        beside = [
            w
            for w in words
            if w.page == anchor.page
            and abs(w.y - anchor.y) < 2.5
            and 0 < abs(w.x - anchor.x) < 22
            and name(w) in names
        ]
        if beside:
            return name(min(beside, key=lambda w: abs(w.x - anchor.x)))
        if self.placement != "cell":
            return None
        above = [
            w
            for w in words
            if w.page == anchor.page
            and 0 < w.y - anchor.y < 150
            and abs(w.x - anchor.x) < 6
            and name(w) in names
        ]
        if not above:
            return None
        return name(min(above, key=lambda w: w.y - anchor.y))

    def _months_from_headings(
        self, words: list[PdfTextFragment], anchors: list[_Anchor]
    ) -> tuple[dict[_Anchor, int], int | None]:
        """Bind each day number to the month heading of its column.

        Also returns the month of the first heading, top left of the first page.
        """
        headings = [
            (w.page, w.x, w.y, month)
            for w in [*words, *_letter_spaced(words)]
            if (month := _month_of(w.text)) is not None
        ]
        # A band is a row of at least two headings; prose mentioning a month
        # ("Mai") on its own is not a heading.
        bands: list[tuple[int, float, list[tuple[float, int]]]] = []
        for page, x, y, month in sorted(headings, key=lambda h: (h[0], -h[2])):
            if bands and bands[-1][0] == page and abs(bands[-1][1] - y) < 4:
                # Some PDFs draw their text twice (a shadow or an overlay).
                if not any(m == month and abs(x0 - x) < 3 for x0, m in bands[-1][2]):
                    bands[-1][2].append((x, month))
            else:
                bands.append((page, y, [(x, month)]))
        # ... and its months follow each other left to right at a column's
        # spacing, which also tells a heading row from a sentence naming two
        # months ("du 1er mars au 31 octobre"). A heading printed as artwork
        # leaves a gap, filled in from that spacing.
        completed = []
        for page, y, columns in bands:
            below = [a for a in anchors if a.page == page and a.y < y]
            if len(columns) > 1 and (filled := _fill_columns(sorted(columns), below)):
                completed.append((page, y, filled))
        bands = completed
        if not bands:
            return {}, None

        # Every day number belongs to the nearest heading row above it.
        under: dict[int, list[_Anchor]] = {}
        for anchor in anchors:
            above = [
                (index, band)
                for index, band in enumerate(bands)
                if band[0] == anchor.page and band[1] > anchor.y
            ]
            if above:
                index, _ = min(above, key=lambda item: item[1][1] - anchor.y)
                under.setdefault(index, []).append(anchor)

        blocks: dict[tuple[int, int], list[_Anchor]] = {}
        months: dict[_Anchor, int] = {}
        for index, band_anchors in under.items():
            columns = bands[index][2]
            for anchor, column in _columns_of(band_anchors, [x for x, _ in columns]):
                months[anchor] = columns[column][1]
                blocks.setdefault((index, column), []).append(anchor)

        # A month grid often prints the previous month's last days before the
        # 1st and the next month's first days after its last: they belong to
        # the neighbouring block, which has its own.
        for block in blocks.values():
            first = [a.y for a in block if a.day == 1]
            last = [a.y for a in block if a.day >= 28]
            for anchor in block:
                if (first and anchor.day > 20 and anchor.y >= max(first) - 2) or (
                    last and anchor.day < 8 and anchor.y <= min(last) + 2
                ):
                    months.pop(anchor, None)
        return months, bands[0][2][0][1]

    def _months_from_columns(self, anchors: list[_Anchor]) -> dict[_Anchor, int]:
        """Number the day-row columns in reading order, from ``first_month``.

        A column is a vertical run of day numbers 1, 2, 3, ... sharing one x;
        runs whose tops are level form a band, read left to right.
        """
        stacks: dict[tuple[int, int], list[_Anchor]] = {}
        for anchor in sorted(anchors, key=lambda a: (a.page, a.x)):
            key = next(
                (
                    k
                    for k in stacks
                    if k[0] == anchor.page and abs(k[1] - anchor.x) <= 3
                ),
                (anchor.page, round(anchor.x)),
            )
            stacks.setdefault(key, []).append(anchor)

        runs: list[list[_Anchor]] = []
        for stack in stacks.values():
            current: list[_Anchor] = []
            for anchor in sorted(stack, key=lambda a: -a.y):
                if current and anchor.day == current[-1].day + 1:
                    current.append(anchor)
                    continue
                if len(current) >= 28:
                    runs.append(current)
                current = [anchor] if anchor.day == 1 else []
            if len(current) >= 28:
                runs.append(current)

        bands: list[list[list[_Anchor]]] = []
        for run in sorted(runs, key=lambda r: (r[0].page, -r[0].y)):
            top = run[0]
            if (
                bands
                and bands[-1][0][0].page == top.page
                and abs(bands[-1][0][0].y - top.y) < 30
            ):
                bands[-1].append(run)
            else:
                bands.append([run])

        months: dict[_Anchor, int] = {}
        index = 0
        for band in bands:
            for run in sorted(band, key=lambda r: r[0].x):
                month = ((self.first_month or 1) - 1 + index) % 12 + 1
                index += 1
                for anchor in run:
                    months[anchor] = month
        return months


def _fill_columns(
    columns: list[tuple[float, int]], anchors: list[_Anchor]
) -> list[tuple[float, int]] | None:
    """A heading row's columns with the missing months filled in, or None.

    ``columns`` are the ``(x, month)`` headings found, left to right. They must
    advance by whole months at one spacing (at least 30 points, a column's
    width rather than a word's); the months between two headings, and those
    beyond the outermost ones that still have day numbers below them, are
    placed at that spacing.
    """
    unwrapped: list[tuple[float, int]] = []
    for x, month in columns:
        while unwrapped and month <= unwrapped[-1][1]:
            month += 12
        unwrapped.append((x, month))
    steps = [(b[0] - a[0]) / (b[1] - a[1]) for a, b in itertools.pairwise(unwrapped)]
    spacing = min(steps)
    if spacing < 30 or max(steps) > spacing * 1.15:
        return None

    first_x, first_month = unwrapped[0]
    last_x, last_month = unwrapped[-1]

    def occupied(x: float) -> bool:
        return any(abs(a.x - x) < spacing / 2 for a in anchors)

    while last_month - first_month < 11 and occupied(last_x + spacing):
        last_x, last_month = last_x + spacing, last_month + 1
    while last_month - first_month < 11 and occupied(first_x - spacing):
        first_x, first_month = first_x - spacing, first_month - 1
    return [
        (first_x + (month - first_month) * spacing, (month - 1) % 12 + 1)
        for month in range(first_month, last_month + 1)
    ]


def _columns_of(
    anchors: list[_Anchor], heading_xs: list[float]
) -> list[tuple[_Anchor, int]]:
    """Each day number under a heading row with the index of its heading.

    The day numbers fall into blocks, split by the gaps between their columns
    that are clearly wider than the spacing inside a block. A block belongs to
    the heading nearest its left edge or its centre, which holds whether a
    heading is centred over its block or set flush left (and when a block has
    no day numbers in the text layer at all). Without such gaps (one column per
    month) a day number belongs to the nearest heading, splitting halfway
    between them.
    """
    xs = sorted({round(a.x) for a in anchors})
    merged: list[float] = []
    for x in xs:
        if not merged or x - merged[-1] > 3:
            merged.append(x)
    steps = [b - a for a, b in itertools.pairwise(merged)]
    if len(heading_xs) > 1 and steps:
        typical = sorted(steps)[len(steps) // 2]
        bounds = [
            (a + b) / 2 for a, b in itertools.pairwise(merged) if b - a > 1.6 * typical
        ]
        if bounds and len(bounds) + 1 >= len(heading_xs) - 1:
            edges = [-float("inf"), *bounds, float("inf")]
            result: list[tuple[_Anchor, int]] = []
            for lo_edge, hi_edge in itertools.pairwise(edges):
                group = [a for a in anchors if lo_edge <= a.x < hi_edge]
                if not group:
                    continue
                lo = min(a.x for a in group)
                centre = (lo + max(a.x for a in group)) / 2
                column = min(
                    range(len(heading_xs)),
                    key=lambda i: min(
                        abs(heading_xs[i] - lo), abs(heading_xs[i] - centre)
                    ),
                )
                result.extend((a, column) for a in group)
            return result
    mids = [(heading_xs[i] + heading_xs[i + 1]) / 2 for i in range(len(heading_xs) - 1)]
    return [(a, sum(1 for mid in mids if a.x >= mid)) for a in anchors]


def _letter_spaced(words: list[PdfTextFragment]) -> list[PdfTextFragment]:
    """Words set letter by letter ("J A N U A R Y"), joined into one each.

    Letters on one baseline at most 12 points apart join up; a weekday header
    row ("S M T W T F S") is set wider apart than that and stays as it is.
    """
    letters = sorted(
        (w for w in words if len(w.text) == 1 and w.text.isalpha()),
        key=lambda w: (w.page, round(w.y), w.x),
    )
    joined: list[PdfTextFragment] = []
    run: list[PdfTextFragment] = []

    def flush() -> None:
        if len(run) >= 3:
            joined.append(
                PdfTextFragment(
                    run[0].page,
                    "".join(w.text for w in run),
                    (run[0].x + run[-1].x) / 2,
                    run[0].y,
                )
            )
        run.clear()

    for letter in letters:
        if run and (
            letter.page != run[-1].page
            or abs(letter.y - run[-1].y) > 1
            or letter.x - run[-1].x > 12
        ):
            flush()
        run.append(letter)
    flush()
    return joined
