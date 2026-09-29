import re
from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
    ArcGisWebMapExpression,
)
from waste_collection_schedule.transformers import ICSTransformer

# Miami-Dade Solid Waste "Garbage and Recycling Pickup Days" layers (public, no
# login). Garbage routes carry the collection weekday(s) directly. Recycling
# routes only name a cycle (A/B/C) and a weekday (DAYID 1-5); the anchor date of
# each cycle and the Christmas delay live in the "Recycle Pick up Days" Arcade
# expression of the county's public web map.
GARBAGE_LAYER = (
    "https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/"
    "GarbagePickupRoute_gdb/FeatureServer/0"
)
RECYCLING_LAYER = (
    "https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/"
    "RecyclingRoute_gdb/FeatureServer/0"
)
WEBMAP_DATA_URL = (
    "https://www.arcgis.com/sharing/rest/content/items/"
    "2e6d2b7bcc854e1e89d953c439ffd917/data"
)
EXPRESSION_TITLE = "Recycle Pick up Days"

LAYERS = [("Garbage", GARBAGE_LAYER), ("Recycling", RECYCLING_LAYER)]

_TYPE_MAP = {
    "Garbage": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
}

WEEKS_AHEAD = 26

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _base_dates(expression: str) -> dict[tuple[str, str], date]:
    """Read the ``(route, routeDay) -> anchor date`` table out of the expression.

    Arcade months run 0-11, so ``Date(2008, 5, 30)`` is 30 June 2008.
    """
    bases: dict[tuple[str, str], date] = {}
    route = route_day = None
    for line in expression.splitlines():
        if m := re.search(r'route == "([ABC])"', line):
            route, route_day = m.group(1), None
        elif m := re.search(r'routeDay == "([1-5])"', line):
            route_day = m.group(1)
        elif route and route_day:
            if m := re.search(r"Date\((\d{4}),\s*(\d{1,2}),\s*(\d{1,2})\)", line):
                year, month, day = (int(g) for g in m.groups())
                bases[(route, route_day)] = date(year, month + 1, day)
                route_day = None
    return bases


def _holiday_delays(expression: str) -> list[tuple[int, int, int]]:
    """Read the ``(month, day, delay days)`` rules, e.g. Christmas + 2 days."""
    delays = []
    for m in re.finditer(
        r"pickupMonth\s*==\s*(\d+)\s*&&\s*pickupDay\s*==\s*(\d+)", expression
    ):
        delay = re.search(
            r'DateAdd\(nextPickupDate,\s*(\d+),\s*"days"\)',
            expression[m.end() :],
        )
        if delay:
            delays.append((int(m.group(1)) + 1, int(m.group(2)), int(delay.group(1))))
    return delays


def _describe(record, source):
    """Turn a garbage or recycling route into Schedule descriptors.

    Garbage recurs weekly on each weekday of the route. Recycling recurs on a
    7-day (route C) or 14-day (routes A, B) cycle from the county's anchor date;
    a collection that lands on a holiday the expression delays is moved.
    """
    label, attrs, expression = record
    if label == "Garbage":
        for name in str(attrs.get("WEEKDAYS") or "").replace(",", " ").split():
            weekday = _WEEKDAYS.get(name.lower())
            if weekday is not None:
                yield Schedule(
                    label,
                    recurrence.next_weekday(weekday),
                    recurrence.WEEKLY,
                    WEEKS_AHEAD,
                )
        return

    bases = _base_dates(expression or "")
    if not bases:
        raise ArcGisError("could not read the recycling anchor dates")
    route = str(attrs.get("PICKUPWEEK") or "").upper()
    base = bases.get((route, str(attrs.get("DAYID") or "")))
    if base is None:
        raise SourceArgumentNotFound("address", str(attrs.get("ROUTE") or ""))

    step = recurrence.WEEKLY if route == "C" else recurrence.FORTNIGHTLY
    dates = recurrence.recurring_from_anchor(
        base, step, WEEKS_AHEAD // (step.days // 7)
    )
    delays = _holiday_delays(expression or "")
    exclude, extra = [], []
    for d in dates:
        for month, day, days in delays:
            if (d.month, d.day) == (month, day):
                exclude.append(d)
                extra.append(d + timedelta(days=days))
    yield Schedule(label, dates[0], step, len(dates), exclude=exclude, extra=extra)


@final
class Source(BaseSource):
    TITLE = "Miami-Dade County"
    DESCRIPTION = "Source for Miami-Dade County garbage and recycling pickup."
    URL = "https://www.miamidade.gov/global/solidwaste/home.page"
    COUNTRY = "us"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@barrelcollector"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "9232 SW 148th Ct": {"address": "9232 SW 148th Ct, Miami, FL 33196"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full street address including city, state and ZIP code "
            "(e.g. '9232 SW 148th Ct, Miami, FL 33196'). It is matched against the "
            "county's Garbage and Recycling Pickup Days routes "
            "(https://gisweb.miamidade.gov/garbageandrecyclingpickupdays/)."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    retrieve = ArcGisMultiFeatureRetriever(LAYERS, address="address")
    parse = ArcGisMultiFeatureParser(first_per_layer=True)
    preprocess = Compose(
        ArcGisWebMapExpression(
            WEBMAP_DATA_URL, EXPRESSION_TITLE, labels=("Recycling",)
        ),
        RecurrenceExpander(_describe),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
