"""Upper Lachlan's published, colour-coded annual collection calendar.

Crookwell's two recycling rounds share a legend colour but use different days.
Only recycling is filtered by that choice. Weekly garbage weekdays are read
from the PDF's header; no recurrence is extended beyond the published year.
"""

import calendar
import re
from collections.abc import Iterable
from datetime import date
from io import BytesIO
from typing import ClassVar, NamedTuple, final

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTChar, LTContainer, LTCurve, LTTextLineHorizontal
from waste_collection_schedule import parsers, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://upperlachlan.nsw.gov.au/services/waste/"
_MONTHS = {
    name.upper(): number for number, name in enumerate(calendar.month_name) if name
}
_WEEKDAYS = {name.upper(): number for number, name in enumerate(calendar.day_name)}
_ROUTES = {
    "Crookwell - Monday recycling": ("CROOKWELL", 0),
    "Crookwell - Tuesday recycling": ("CROOKWELL", 1),
    **{
        name: (name.upper(), None)
        for name in (
            "Binda",
            "Breadalbane",
            "Collector",
            "Dalton",
            "Golspie",
            "Grabben Gullen",
            "Gunning",
            "Laggan",
            "Taralga",
        )
    },
    "Lost River - recycling only": ("LOST RIVER", None),
}


class _Layout(NamedTuple):
    lines: list[parsers.PdfTextFragment]
    words: list[parsers.PdfTextFragment]
    vectors: list[parsers.PdfVector]


def _colour(value) -> tuple[float, ...] | None:
    if isinstance(value, (float, int)):
        return (float(value),) * 3
    return tuple(value) if isinstance(value, (tuple, list)) else None


def _parse_pdf(response, source: BaseSource | None = None) -> _Layout:
    """Keep individual date coordinates, including words merged into text lines.

    This PDF resets pypdf text matrices to (0, 0) for most dates, while
    PdfTableParser groups adjacent cells into one run. pdfminer's character
    coordinates retain the exact cell positions needed to join text to fills.
    """
    lines, words, vectors = [], [], []

    def visit(item, page):
        if isinstance(item, LTTextLineHorizontal):
            lines.append(
                parsers.PdfTextFragment(
                    page,
                    " ".join(item.get_text().split()),
                    (item.x0 + item.x1) / 2,
                    (item.y0 + item.y1) / 2,
                )
            )
            chars = []

            def flush():
                if chars:
                    words.append(
                        parsers.PdfTextFragment(
                            page,
                            "".join(c.get_text() for c in chars),
                            (chars[0].x0 + chars[-1].x1) / 2,
                            (chars[0].y0 + chars[0].y1) / 2,
                        )
                    )
                    chars.clear()

            for char in item:
                if isinstance(char, LTChar) and not char.get_text().isspace():
                    chars.append(char)
                else:
                    flush()
            flush()
        elif isinstance(item, LTContainer):
            for child in item:
                visit(child, page)
        elif isinstance(item, LTCurve) and item.fill:
            vectors.append(
                parsers.PdfVector(
                    page,
                    item.x0,
                    item.y0,
                    item.x1,
                    item.y1,
                    _colour(item.stroking_color),
                    _colour(item.non_stroking_color),
                )
            )

    for page, layout in enumerate(
        extract_pages(BytesIO(response.content), laparams=LAParams())
    ):
        visit(layout, page)
    response_shape.expect(
        len(words) > 365 and bool(vectors),
        source_name=response_shape.source_name(source),
        detail="annual calendar text or coloured cells missing",
        raw=str(lines[:10]),
    )
    return _Layout(lines, words, vectors)


def _fill(layout: _Layout, word: parsers.PdfTextFragment) -> tuple[float, ...] | None:
    matches = [
        v
        for v in layout.vectors
        if v.page == word.page and v.x0 < word.x < v.x1 and v.y0 < word.y < v.y1
    ]
    if not matches:
        return None
    return min(matches, key=lambda v: (v.x1 - v.x0) * (v.y1 - v.y0)).fill_color


def _current_calendar(matches: list[re.Match]) -> re.Match:
    # Prefer this year even when next year's PDF has already been published.
    current = [m for m in matches if int(m.group(1)) == date.today().year]
    response_shape.expect(
        bool(current),
        source_name="Upper Lachlan Shire Council",
        detail="no calendar published for the current year",
        raw=[m.string for m in matches],
    )
    return current[0]


def _calendar_rows(layout: _Layout, source: BaseSource) -> Iterable[tuple[date, str]]:
    locality, recycling_day = _ROUTES[source.params["route"]]
    name = response_shape.source_name(source)

    def expect(condition, detail):
        response_shape.expect(
            condition, source_name=name, detail=detail, raw=str(layout.lines[:10])
        )

    years = {int(w.text) for w in layout.words if re.fullmatch(r"20\d{2}", w.text)}
    expect(len(years) == 1, "could not identify one calendar year")
    year = years.pop()
    months = [w for w in layout.words if w.text in _MONTHS]
    expect(
        len(months) == 12 and len({w.text for w in months}) == 12,
        "expected all twelve month headings",
    )
    legend = {}
    palette = {}
    garbage_day = None
    for line in layout.lines:
        text = line.text.upper()
        local = bool(re.search(rf"\b{re.escape(locality)}\b", text))
        if match := re.fullmatch(r"(\w+)\s*-\s*(.+)", text):
            if local and match.group(1) in _WEEKDAYS:
                garbage_day = _WEEKDAYS[match.group(1)]
        for suffix, waste_type in (
            (" RECYCLE", "Recycling"),
            (" GARDEN WASTE", "Garden waste"),
        ):
            if text.endswith(suffix):
                colour = _fill(layout, line)
                expect(
                    colour is not None and colour not in palette,
                    "missing or ambiguous legend colour",
                )
                palette[colour] = text
                if local:
                    legend[text] = waste_type
    expect(
        "Recycling" in legend.values(), "recycling legend missing for selected route"
    )
    if locality != "LOST RIVER":
        expect(
            "Garden waste" in legend.values() and garbage_day is not None,
            "garden-waste legend or weekly garbage day missing for selected route",
        )

    days = {}
    for month in months:
        # Sunday-first headings define each seven-column month grid. Their
        # positions, not fixed PDF coordinates, determine the calendar bounds.
        headings = [
            w
            for w in layout.words
            if w.page == month.page and w.text in "SMTWF" and 0 < month.y - w.y < 15
        ]
        headings.sort(key=lambda w: w.x)
        expect(len(headings) == 21, "expected three Sunday-first weekday grids")
        peers = sorted(
            [m for m in months if m.page == month.page and abs(m.y - month.y) < 2],
            key=lambda m: m.x,
        )
        expect(len(peers) == 3, "expected three months per calendar row")
        columns = headings[peers.index(month) * 7 : peers.index(month) * 7 + 7]
        expect("".join(w.text for w in columns) == "SMTWTFS", "weekday grid changed")
        step = (columns[-1].x - columns[0].x) / 6
        left, right = columns[0].x - step / 2, columns[-1].x + step / 2
        lower = max(
            (m.y for m in months if m.page == month.page and m.y < month.y - 2),
            default=0,
        )
        candidates = [
            w
            for w in layout.words
            if w.page == month.page
            and w.text.isdigit()
            and left < w.x < right
            and lower < w.y < columns[0].y
        ]
        month_days = set()
        for word in candidates:
            day = int(word.text)
            expect(
                1 <= day <= calendar.monthrange(year, _MONTHS[month.text])[1],
                "invalid day in month grid",
            )
            when = date(year, _MONTHS[month.text], day)
            column = min(range(7), key=lambda i: abs(columns[i].x - word.x))
            expect(
                when.weekday() == (column + 6) % 7,
                f"date is in the wrong weekday column: {when}",
            )
            expect(day not in month_days, f"duplicate date in month grid: {when}")
            month_days.add(day)
            colour = _fill(layout, word)
            # The PDF uses slightly different shades in its legend and cells,
            # including a grey RGB legend with greyscale day cells.
            matches = [
                label
                for key, label in palette.items()
                if colour is not None
                and len(colour) == len(key)
                and max(abs(a - b) for a, b in zip(colour, key, strict=True)) <= 0.075
            ]
            expect(
                (colour is None and not matches) or len(matches) == 1,
                f"unknown or ambiguous calendar colour on {when}",
            )
            days[when] = matches[0] if matches else None
        expect(
            len(month_days) == calendar.monthrange(year, _MONTHS[month.text])[1],
            f"incomplete {month.text} grid",
        )

    found = set()
    for when, colour in sorted(days.items()):
        if garbage_day == when.weekday():
            yield when, "General waste"
        if colour in legend:
            waste_type = legend[colour]
            if (
                waste_type == "Recycling"
                and recycling_day is not None
                and when.weekday() != recycling_day
            ):
                continue
            found.add(waste_type)
            yield when, waste_type
    expect(
        found == set(legend.values()),
        "calendar contains no dates for a selected waste stream",
    )


@final
class Source(BaseSource):
    TITLE = "Upper Lachlan Shire Council"
    DESCRIPTION = "Waste collections for Upper Lachlan Shire Council, NSW."
    URL = _URL
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]
    TEST_CASES: ClassVar[dict] = {
        route: {"route": route}
        for route in (
            "Crookwell - Monday recycling",
            "Crookwell - Tuesday recycling",
            "Gunning",
            "Taralga",
            "Binda",
            "Lost River - recycling only",
        )
    }
    PARAMS = (
        dropdown("route", list(_ROUTES), label="Collection area / recycling route"),
    )
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Choose your serviced locality. In Crookwell, choose your street's Monday or Tuesday recycling round; this does not change other bin days. Check your route with council if unsure. Lost River supplies recycling only because the calendar does not specify its other services. Dates follow the council PDF; separate service-disruption notices are not included."
    }
    retrieve = retrievers.PdfLinkRetriever(
        index_url=_URL,
        pattern=r"All-Collection-Areas-(\d{4})\.pdf",
        select=_current_calendar,
    )
    parse = staticmethod(_parse_pdf)
    preprocess = staticmethod(_calendar_rows)
    transform = ICSTransformer(
        type_value_map={
            "General waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden waste": wt.GARDEN_WASTE,
        }
    )
