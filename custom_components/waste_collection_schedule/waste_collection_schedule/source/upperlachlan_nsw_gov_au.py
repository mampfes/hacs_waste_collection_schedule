"""Upper Lachlan's published, colour-coded annual collection calendar.

Crookwell's two recycling rounds share a legend colour but use different days.
Only recycling is filtered by that choice. Weekly garbage weekdays are read
from the PDF's header. Unpublished years carry forward the last confirmed
weekly/fortnightly cycle; a new published calendar always takes precedence.
"""

import calendar
import re
from collections.abc import Iterable
from datetime import date
from typing import ClassVar, final
from urllib.parse import urljoin

from waste_collection_schedule import parsers, recurrence, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.service.ICS import IcsEvent
from waste_collection_schedule.service.PdfWordLayout import (
    PdfWordLayout,
    PdfWordLayoutParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://upperlachlan.nsw.gov.au/services/waste/"
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


def _fill(
    layout: PdfWordLayout, word: parsers.PdfTextFragment
) -> tuple[float, ...] | None:
    matches = [
        v
        for v in layout.vectors
        if v.page == word.page and v.x0 < word.x < v.x1 and v.y0 < word.y < v.y1
    ]
    if not matches:
        return None
    return min(matches, key=lambda v: (v.x1 - v.x0) * (v.y1 - v.y0)).fill_color


def _calendar_urls(response, **_) -> list[str]:
    """Read the latest available anchor year and any published next year."""
    urls = {}
    for link in parsers.HtmlParser("a[href]")(response):
        href = str(link["href"])
        if match := re.search(r"All-Collection-Areas-(\d{4})\.pdf$", href):
            urls[int(match.group(1))] = urljoin(response.url, href)
    current_year = date.today().year
    previous = [year for year in urls if year <= current_year]
    response_shape.expect(
        bool(previous),
        source_name="Upper Lachlan Shire Council",
        detail="no current or previous calendar available to anchor the schedule",
        raw=list(urls.values()),
    )
    latest = max(previous)
    return [urls[year] for year in sorted(urls) if latest <= year <= current_year + 1]


def _collection_rows(
    layouts: list[PdfWordLayout], source: BaseSource
) -> Iterable[IcsEvent]:
    calendars = [list(_calendar_rows(layout, source)) for layout in layouts]
    years = [rows[0][0].year for rows in calendars]
    response_shape.expect(
        len(years) == len(set(years)),
        source_name=response_shape.source_name(source),
        detail="multiple calendar files describe the same year",
        raw=years,
    )
    yield from sorted(
        _carry_forward(calendars, source), key=lambda event: (event.date, event.title)
    )


def _carry_forward(
    calendars: list[list[tuple[date, str]]], source: BaseSource
) -> Iterable[IcsEvent]:
    """Use whole published years, projecting only years without a calendar.

    The service cadence is weekly garbage and fortnightly
    recycling/garden waste. The phase comes from each stream's last published
    date, never a fixed date or ISO week number. Retain published dates and
    extend through the end of next year on every refresh.
    """
    published = {rows[0][0].year: rows for rows in calendars}
    for year in sorted(published):
        for when, waste_type in published[year]:
            yield IcsEvent(when, waste_type)
    for year in range(date.today().year, date.today().year + 2):
        if year in published:
            continue
        anchor_years = [prior for prior in published if prior < year]
        response_shape.expect(
            bool(anchor_years),
            source_name=response_shape.source_name(source),
            detail="no earlier calendar to anchor unpublished year",
            raw=list(published),
        )
        anchor_year = max(anchor_years)
        anchors = {}
        for when, waste_type in published[anchor_year]:
            anchors[waste_type] = max(when, anchors.get(waste_type, when))
        for waste_type, anchor in anchors.items():
            step = (
                recurrence.WEEKLY
                if waste_type == "General waste"
                else recurrence.FORTNIGHTLY
            )
            for when in recurrence.recurring_within(
                anchor, step, not_before=date(year, 1, 1), until=date(year, 12, 31)
            ):
                yield IcsEvent(
                    when,
                    waste_type,
                    description=f"Projected from the {anchor_year} council calendar using the continuing collection cycle. Check council notices for service changes.",
                )


def _calendar_rows(
    layout: PdfWordLayout, source: BaseSource
) -> Iterable[tuple[date, str]]:
    locality, recycling_day = _ROUTES[source.params["route"]]
    name = response_shape.source_name(source)

    def expect(condition, detail):
        response_shape.expect(
            condition, source_name=name, detail=detail, raw=str(layout.lines[:10])
        )

    years = {int(w.text) for w in layout.words if re.fullmatch(r"20\d{2}", w.text)}
    expect(len(years) == 1, "could not identify one calendar year")
    year = years.pop()
    months = [w for w in layout.words if recurrence.month(w.text) is not None]
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
            if local and recurrence.weekday(match.group(1)) is not None:
                garbage_day = recurrence.weekday(match.group(1))
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
        month_number = recurrence.month(month.text)
        if month_number is None:
            raise ValueError(f"Unrecognised month: {month.text}")
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
                1 <= day <= calendar.monthrange(year, month_number)[1],
                "invalid day in month grid",
            )
            when = date(year, month_number, day)
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
            len(month_days) == calendar.monthrange(year, month_number)[1],
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
        "en": "Choose your serviced locality. In Crookwell, choose your street's Monday or Tuesday recycling round; this does not change other bin days. Check your route with council if unsure. Lost River supplies recycling only because the calendar does not specify its other services. Dates follow the council PDF. Where a calendar is not yet published, the last confirmed weekly garbage and fortnightly recycling/garden cycle is carried forward through next year. Those events are marked as projected in their description and are replaced when the new calendar is available. Separate service-disruption notices are not included."
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(_URL, pick=_calendar_urls, raise_for_status=True),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url, raise_for_status=True),
    )
    parse = parsers.EachResponse(PdfWordLayoutParser(min_words=366, min_vectors=1))
    preprocess = staticmethod(_collection_rows)
    transform = ICSTransformer(
        type_value_map={
            "General waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden waste": wt.GARDEN_WASTE,
        }
    )
