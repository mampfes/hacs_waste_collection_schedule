"""Carterton District Council, New Zealand.

The council publishes a yearly urban rubbish and recycling calendar (April to
March) on https://cdc.govt.nz/services/sustainability/recycling/. Its month
grids paint every week red (week 1) or blue (week 2). Rubbish bags go out every
week; the recycling wheelie bin goes out in the week the household's sticker
names (1 or 2) and the glass crates in the other week. A black dot marks a
public holiday and a yellow strip the days a collection moves to, one day
later.

Only some months of the PDF carry their day numbers as text, so the dated cells
give the week rhythm and the holiday moves of those months; the rhythm is then
carried through the season, and the holiday moves of the other months come from
the public holidays of the Wellington region.
"""

import datetime
from collections.abc import Iterable
from typing import ClassVar, final

import holidays
from waste_collection_schedule import config_params, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://cdc.govt.nz"
_INDEX_URL = f"{_URL}/services/sustainability/recycling/"

WEEK_1 = "Week 1"
WEEK_2 = "Week 2"
LATER = "Collection a day later"
HOLIDAY = "Public holiday"

RUBBISH = "Rubbish bags"
RECYCLING = "Recycling wheelie bin"
GLASS = "Glass crates"

_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

_CELL_WIDTH = (17.0, 23.0)
_CELL_HEIGHT = (14.0, 20.0)
_MONTH_HEADING = (
    r"(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER"
    r"|NOVEMBER|DECEMBER)\s+(20\d{2})"
)


def _monday(day: datetime.date) -> datetime.date:
    return day - datetime.timedelta(days=day.weekday())


def _schedule(
    rows: list[tuple[datetime.date, str]], source: BaseSource | None = None
) -> Iterable[tuple[datetime.date, str]]:
    """Expand the week rhythm over the season and apply the holiday moves."""
    name = response_shape.source_name(source)
    weeks = {_monday(day): label for day, label in rows if label in (WEEK_1, WEEK_2)}
    response_shape.expect(
        len(weeks) >= 8,
        source_name=name,
        detail=f"only {len(weeks)} weeks dated in the calendar",
    )
    if not weeks:
        return
    reference = min(weeks)
    reference_label = weeks[reference]

    def week_label(monday: datetime.date) -> str:
        same = ((monday - reference).days // 7) % 2 == 0
        return reference_label if same else ({WEEK_1, WEEK_2} - {reference_label}).pop()

    agree = sum(week_label(monday) == label for monday, label in weeks.items())
    response_shape.expect(
        agree >= 0.95 * len(weeks),
        source_name=name,
        detail="the calendar's weeks do not alternate between week 1 and week 2",
    )

    dated = {day for day, _ in rows}
    later = {day for day, label in rows if label == LATER}
    marked_holidays = {day for day, label in rows if label == HOLIDAY}
    last = max(day for day, _ in rows)
    end = (last.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    start = end.replace(year=end.year - 1)
    regional = holidays.country_holidays(
        "NZ", subdiv="WGN", years=range(start.year, end.year + 1)
    )

    params = source.params if source else {}
    weekday = _DAYS.index(params.get("collection_day") or "Monday")
    bin_week = WEEK_1 if str(params.get("sticker") or "1") == "1" else WEEK_2

    monday = _monday(start)
    while monday < end:
        day = monday + datetime.timedelta(days=weekday)
        if day in dated:
            # A dated day: move as the calendar shows.
            moved = day in marked_holidays or day + datetime.timedelta(days=1) in later
        else:
            moved = any(
                monday + datetime.timedelta(days=offset) in regional
                for offset in range(weekday + 1)
            )
        if start <= day < end:
            if moved:
                day += datetime.timedelta(days=1)
            yield day, RUBBISH
            yield day, RECYCLING if week_label(monday) == bin_week else GLASS
        monday += datetime.timedelta(days=7)


@final
class Source(BaseSource):
    TITLE = "Carterton District Council"
    DESCRIPTION = "Source for Carterton District Council (NZ) urban rubbish and recycling collections."
    URL = _URL
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.GLASS, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Sticker 1, Monday": {"sticker": "1", "collection_day": "Monday"},
        "Sticker 2, Friday": {"sticker": "2", "collection_day": "Friday"},
    }

    PARAMS = (
        config_params.dropdown("sticker", ["1", "2"], label="Sticker"),
        config_params.dropdown("collection_day", _DAYS, label="Collection day"),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "The sticker on your recycling wheelie bin shows a 1 or a 2 and your "
            "collection day. Choose both. Week 1 and week 2 are the red and blue "
            "weeks of the calendar on https://cdc.govt.nz/services/sustainability/recycling/."
        ),
    }

    retrieve = retrievers.PdfLinkRetriever(
        index_url=_INDEX_URL,
        pattern=r"Collection-Calendar-(\d{4})\.pdf",
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(
                WEEK_1, (0.0, 0.9, 1.0, 0.0), width=_CELL_WIDTH, height=_CELL_HEIGHT
            ),
            Marker(
                WEEK_2, (0.32, 0.0, 0.1, 0.0), width=_CELL_WIDTH, height=_CELL_HEIGHT
            ),
            Marker(LATER, (0.0, 0.09, 1.0, 0.0), width=(15, 160), height=(6, 20)),
            Marker(HOLIDAY, (0.0, 0.0, 0.0, 1.0), width=(13, 17), height=(13, 17)),
        ],
        placement="cell",
        weekdays="MTWTFSS",
        first_month=None,
        year_pattern=_MONTH_HEADING,
    )
    preprocess = staticmethod(_schedule)
    transform = ICSTransformer(
        type_value_map={
            RUBBISH: wt.GENERAL_WASTE,
            RECYCLING: wt.RECYCLABLES,
            GLASS: wt.GLASS,
        }
    )
