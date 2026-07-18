import datetime
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.Pozi import (
    PoziGeoJsonParser,
    PoziGeoJsonRetriever,
    geocode_earth,
)
from waste_collection_schedule.transformers import RowTransformer

# Demonstrates: a Pozi GeoJSON zone lookup by address, geocoded first via
# geocode.earth (Frankston's Pozi widget has no address lookup of its own).
# The zone's properties carry, per waste type, a weekday, a weekly/fortnightly
# cadence and a cycle start date; _describe() aligns the next collection date
# to both the weekday and the cadence phase. Labels ("Rubbish", "Recycling",
# "Green Waste", "Glass") all resolve against the shared multilingual
# vocabulary, so no type_value_map is needed.

ZONES_URL = "https://connect.pozi.com/userdata/frankston-publisher/Community/Kerbside_Garbage_Collection_(Widget).json"
GEOCODE_API_KEY = "ge-39bfbedc55be11c0"
GEOCODE_BOUNDARY_GID = "whosonfirst:county:102048609"

# zone property prefix -> waste-type label.
_COLLECTIONS = (
    ("rub", "Rubbish"),
    ("rec", "Recycling"),
    ("grn", "Green Waste"),
    ("gls", "Glass"),
)


def _next_aligned_collection(
    weekday: int, weeks: int, start: datetime.date
) -> datetime.date:
    """The next date on ``weekday`` that also stays in phase with the cadence.

    Frankston publishes a cycle start date and a weekly/fortnightly cadence
    separately from the collection weekday; the next real collection is the
    nearest ``weekday`` on/after today whose distance from ``start`` is a
    whole number of cycles.
    """
    today = datetime.date.today()
    next_collect = today + datetime.timedelta(days=(weekday - today.weekday()) % 7)
    cycle = weeks * 7
    remainder = (next_collect - start).days % cycle
    if remainder != 0:
        next_collect += datetime.timedelta(days=cycle - remainder)
    return next_collect


def _describe(zone, source):
    for prefix, label in _COLLECTIONS:
        day_name = zone.get(f"{prefix}_day")
        weeks_raw = zone.get(f"{prefix}_weeks")
        start_raw = zone.get(f"{prefix}_start")
        if not day_name or not weeks_raw or not start_raw:
            continue

        weekday = recurrence.weekday(day_name)
        if weekday is None:
            continue
        try:
            weeks = int(weeks_raw)
            start = datetime.datetime.strptime(start_raw, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            continue
        if weeks <= 0:
            continue

        next_collect = _next_aligned_collection(weekday, weeks, start)
        yield Schedule(label, next_collect, datetime.timedelta(weeks=weeks), 4 // weeks)


@final
class Source(BaseSource):
    TITLE = "Frankston City Council"
    DESCRIPTION = "Source script for frankston.vic.gov.au"
    URL = "https://frankston.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "45r Wedge Rd": {"address": "45r Wedge Rd, Carrum Downs Vic"},  # Monday
        "300 Wedge Rd": {
            "address": "300 Wedge Rd, Skye Vic"
        },  # Monday, but inverse recycling week to 45r Wedge Rd
        "66 Skye Rd": {"address": "66 Skye Rd, Skye Vic"},  # Tuesday
        "160 North Rd": {"address": "160 North Road, Langwarrin Vic"},  # Wednesday
        "65 Golf Links Rd": {"address": "65 Golf Links Rd, Frankston Vic"},  # Thursday
        "107 Nepean Highway": {"address": "107 Nepean Highway, Seaford Vic"},  # Friday
    }

    PARAMS = (text_field("address", "Street Address"),)

    retrieve = PoziGeoJsonRetriever(
        ZONES_URL,
        address="address",
        geocode=lambda address, source: geocode_earth(
            address,
            source,
            api_key=GEOCODE_API_KEY,
            boundary_gid=GEOCODE_BOUNDARY_GID,
        ),
    )
    parse = PoziGeoJsonParser()
    preprocess = RecurrenceExpander(_describe)
    transform = RowTransformer()

    def __init__(self, address: str):
        super().__init__(address=address)
