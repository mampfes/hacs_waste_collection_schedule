"""Lakeshore Recycling Systems (LRS), Illinois, USA.

LRS publishes a yearly "Waste & Recycling Service" calendar PDF for each
municipality it serves (for example Bannockburn). Its month grids paint the
recycling days green (recycling service A) or grey-blue (recycling service B),
the e-waste event days yellow and the observed holidays orange; a holiday
from Monday to Friday delays the rest of that week's collections by one day,
which the recycling cells already show. Waste is collected every week on the
service day.
"""

import datetime
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import config_params, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.lrsrecycles.com"

SERVICE_A = "A"
SERVICE_B = "B"
E_WASTE = "E-waste event"
HOLIDAY = "Holiday"

WASTE = "Waste"
RECYCLING = "Recycling"

_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
_CELL = (15.0, 20.0)


def _sunday(day: datetime.date) -> datetime.date:
    return day - datetime.timedelta(days=(day.weekday() + 1) % 7)


def _schedule(
    rows: list[tuple[datetime.date, str]], source: BaseSource | None = None
) -> Iterable[tuple[datetime.date, str]]:
    """Weekly waste, recycling in the household's service week, e-waste events."""
    params = source.params if source else {}
    offset = _DAYS.index(params.get("service_day") or "Monday") + 1
    service = (params.get("recycling_service") or SERVICE_A).upper()

    holidays = {day for day, label in rows if label == HOLIDAY}
    recycling = {day for day, label in rows if label == service}
    first = min(day for day, _ in rows)
    last = max(day for day, _ in rows)

    sunday = _sunday(first)
    while sunday <= last:
        day = sunday + datetime.timedelta(days=offset)
        if any(
            sunday + datetime.timedelta(days=d) in holidays
            for d in range(1, offset + 1)
        ):
            day += datetime.timedelta(days=1)
        if first <= day <= last and day not in holidays:
            yield day, WASTE
            if day in recycling:
                yield day, RECYCLING
        sunday += datetime.timedelta(days=7)

    for day, label in rows:
        if label == E_WASTE:
            yield day, E_WASTE


@final
class Source(BaseSource):
    TITLE = "Lakeshore Recycling Systems (LRS)"
    DESCRIPTION = "Source for Lakeshore Recycling Systems (Illinois) municipal waste and recycling calendars."
    URL = _URL
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.ELECTRONICS, wt.GENERAL_WASTE, wt.RECYCLABLES]

    _BANNOCKBURN_2026 = (
        "https://www.lrsrecycles.com/municipality/_shared/pdfs/"
        "d6b92e8267e711a9766eead69edb0a66.pdf"
    )

    TEST_CASES: ClassVar[dict] = {
        "Bannockburn, Monday A": {
            "calendar_url": _BANNOCKBURN_2026,
            "service_day": "Monday",
            "recycling_service": "A",
        },
        "Bannockburn, Tuesday B": {
            "calendar_url": _BANNOCKBURN_2026,
            "service_day": "Tuesday",
            "recycling_service": "B",
        },
    }

    PARAMS = (
        config_params.text_field("calendar_url", "Calendar PDF URL"),
        config_params.dropdown("service_day", _DAYS, label="Service day"),
        config_params.dropdown(
            "recycling_service", [SERVICE_A, SERVICE_B], label="Recycling service"
        ),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Copy the link of your municipality's 'Waste & Recycling Service' "
            "calendar PDF from LRS (lrsrecycles.com or your village's website) "
            "into `calendar_url`; LRS publishes a new link every year. The map "
            "on the calendar shows your service day and whether your recycling "
            "service is A or B."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(
        url=lambda calendar_url, **_: calendar_url, timeout=60
    )
    parse = MarkerCalendarParser(
        [
            Marker(SERVICE_A, (0.42, 0.76, 0.29), width=_CELL, height=_CELL),
            Marker(SERVICE_B, (0.47, 0.53, 0.63), width=_CELL, height=_CELL),
            Marker(E_WASTE, (1.0, 0.83, 0.23), width=_CELL, height=_CELL),
            Marker(HOLIDAY, (0.91, 0.33, 0.14), width=_CELL, height=_CELL),
        ],
        placement="cell",
        weekdays="MTWTFSS",
        pages=(0,),
        include_form_text=True,
        year_pattern=r"(20\d{2})\s+Calendar",
    )
    preprocess = staticmethod(_schedule)
    transform = ICSTransformer(
        type_value_map={
            WASTE: wt.GENERAL_WASTE,
            RECYCLING: wt.RECYCLABLES,
            E_WASTE: wt.ELECTRONICS,
        }
    )
