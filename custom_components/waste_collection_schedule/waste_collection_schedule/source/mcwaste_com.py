"""McNamara Waste Services, Massachusetts, USA.

McNamara serves Hampden, Wilbraham, Palmer, Belchertown, Ware, Warren and
Brimfield. Its yearly trash and recycling calendar, linked from
https://www.mcwaste.com/, paints every week (Sunday to Saturday) grey for an
A week or pink for a B week, and the observed holidays red. Trash goes out
every week, recycling every other week, in the household's A or B week; a
holiday from Monday to Friday delays the rest of that week's collections by
one day.
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

_URL = "https://www.mcwaste.com"

A_WEEK = "A"
B_WEEK = "B"
HOLIDAY = "Holiday"

TRASH = "Trash"
RECYCLING = "Recycling"

_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def _sunday(day: datetime.date) -> datetime.date:
    return day - datetime.timedelta(days=(day.weekday() + 1) % 7)


def _schedule(
    rows: list[tuple[datetime.date, str]], source: BaseSource | None = None
) -> Iterable[tuple[datetime.date, str]]:
    """The household's trash and recycling days, delayed after a holiday."""
    votes: dict[datetime.date, Counter] = {}
    for day, label in rows:
        if label in (A_WEEK, B_WEEK):
            votes.setdefault(_sunday(day), Counter())[label] += 1
    response_shape.expect(
        len(votes) >= 40,
        source_name=response_shape.source_name(source),
        detail=f"only {len(votes)} A/B weeks found in the calendar",
    )
    weeks = {sunday: count.most_common(1)[0][0] for sunday, count in votes.items()}
    holidays = {day for day, label in rows if label == HOLIDAY}

    params = source.params if source else {}
    offset = _DAYS.index(params.get("collection_day") or "Monday") + 1
    recycling_week = (params.get("recycling_week") or A_WEEK).upper()

    first = min(day for day, _ in rows)
    last = max(day for day, _ in rows)
    for sunday, label in sorted(weeks.items()):
        day = sunday + datetime.timedelta(days=offset)
        if not first <= day <= last:
            continue
        if any(
            sunday + datetime.timedelta(days=d) in holidays
            for d in range(1, offset + 1)
        ):
            day += datetime.timedelta(days=1)
        yield day, TRASH
        if label == recycling_week:
            yield day, RECYCLING


@final
class Source(BaseSource):
    TITLE = "McNamara Waste Services"
    DESCRIPTION = "Source for McNamara Waste Services (Massachusetts) trash and recycling collection."
    URL = _URL
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Tuesday, A week": {"collection_day": "Tuesday", "recycling_week": "A"},
        "Friday, B week": {"collection_day": "Friday", "recycling_week": "B"},
    }

    PARAMS = (
        config_params.dropdown("collection_day", _DAYS, label="Collection day"),
        config_params.dropdown(
            "recycling_week", [A_WEEK, B_WEEK], label="Recycling week"
        ),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Choose your trash day and your recycling week (A or B). The town "
            "lists linked from https://www.mcwaste.com/ (Hampden, Wilbraham) give "
            "both for every street; elsewhere ask McNamara (413-566-8322)."
        ),
    }

    retrieve = retrievers.PdfLinkRetriever(
        index_url=f"{_URL}/",
        pattern=r"/(\d{4})\+mcnamara[^/]*calendar[^/]*\.pdf",
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            # A week painted over several days (or over the same row of two
            # neighbouring months) is one bar.
            Marker(A_WEEK, (0.16, 0.12, 0.12, 0.0), width=(20, 400), height=(10, 16)),
            Marker(B_WEEK, (0.24, 0.6, 0.36, 0.01), width=(20, 400), height=(10, 16)),
            Marker(HOLIDAY, (0.0, 0.92, 0.78, 0.0), width=(20, 30), height=(10, 16)),
        ],
        placement="cell",
        weekdays="MTWTFSS",
        year_pattern=r"(20\d{2})",
    )
    preprocess = staticmethod(_schedule)
    transform = ICSTransformer(
        type_value_map={TRASH: wt.GENERAL_WASTE, RECYCLING: wt.RECYCLABLES}
    )
