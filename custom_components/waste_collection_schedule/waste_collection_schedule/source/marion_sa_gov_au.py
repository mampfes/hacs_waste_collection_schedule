"""City of Marion, South Australia.

The council publishes a yearly kerbside bin collection calendar PDF on
https://www.marion.sa.gov.au/services-we-offer/waste-and-recycling/bin-collection-and-calendar.
Calendar A (page 3)
and calendar B (page 4) each list their suburbs by collection weekday and paint
every week of their month grids green (organics week) or yellow (recycling
week); the waste bin goes out every week. There is no collection on New
Year's Day or Christmas Day: in those weeks the collection takes place the day
after the normal collection day from that day on.
"""

import datetime
from collections import Counter
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import config_params, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.marion.sa.gov.au"
_INDEX_URL = f"{_URL}/services-we-offer/waste-and-recycling/bin-collection-and-calendar"

ORGANICS = "Organics week"
RECYCLING = "Recycling week"
WASTE = "Waste"

# Calendar -> its page in the PDF.
_CALENDARS = {"A": 2, "B": 3}
_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def _schedule(
    rows: list[tuple[datetime.date, str]], source: BaseSource | None = None
) -> Iterable[tuple[datetime.date, str]]:
    """Weekly waste, and the organics or recycling bin of each week."""
    weekday = _DAYS.index(source.params["collection_day"] if source else "Monday")
    votes: dict[datetime.date, Counter] = {}
    for day, label in rows:
        if day.weekday() < 5:
            monday = day - datetime.timedelta(days=day.weekday())
            votes.setdefault(monday, Counter())[label] += 1
    response_shape.expect(
        len(votes) >= 45,
        source_name=response_shape.source_name(source),
        detail=f"only {len(votes)} weeks found in the calendar",
    )
    first = min(day for day, _ in rows)
    last = max(day for day, _ in rows)
    for monday, count in sorted(votes.items()):
        day = monday + datetime.timedelta(days=weekday)
        if not first <= day <= last:
            continue
        closed = [
            monday + datetime.timedelta(days=d)
            for d in range(weekday + 1)
            if (monday + datetime.timedelta(days=d)).strftime("%m-%d")
            in ("01-01", "12-25")
        ]
        if closed:
            day += datetime.timedelta(days=1)
        yield day, WASTE
        yield day, count.most_common(1)[0][0]


@final
class Source(BaseSource):
    TITLE = "City of Marion"
    DESCRIPTION = (
        "Source for City of Marion (South Australia) kerbside bin collections."
    )
    URL = _URL
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Sheidow Park (B, Monday)": {"calendar": "B", "collection_day": "Monday"},
        "Marion (A, Thursday)": {"calendar": "A", "collection_day": "Thursday"},
    }

    PARAMS = (
        config_params.dropdown("calendar", list(_CALENDARS), label="Calendar"),
        config_params.dropdown("collection_day", _DAYS, label="Collection day"),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Open the kerbside bin collection calendar linked from "
            "https://www.marion.sa.gov.au/services-we-offer/waste-and-recycling/bin-collection-and-calendar. "
            "Calendar A and calendar B each list their suburbs under the "
            "collection weekday; choose the calendar and weekday listing your "
            "suburb. In Hallett Cove the map on calendar B shows your area."
        ),
    }

    retrieve = retrievers.PdfLinkRetriever(
        index_url=_INDEX_URL,
        pattern=r"Kerbside-?Calendar[^/]*\.pdf",
        select="first",
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(ORGANICS, (0.77, 0.86, 0.61), width=(10, 16), height=(9, 14)),
            Marker(RECYCLING, (1.0, 0.82, 0.38), width=(10, 16), height=(9, 14)),
        ],
        placement="cell",
        weekdays="MTWTFSS",
        pages=lambda calendar, **_: (_CALENDARS[calendar],),
        year_pattern=r"(20\d{2})\s+KERBSIDE",
    )
    preprocess = staticmethod(_schedule)
    transform = ICSTransformer(
        type_value_map={
            WASTE: wt.GENERAL_WASTE,
            ORGANICS: wt.ORGANIC,
            RECYCLING: wt.RECYCLABLES,
        }
    )
