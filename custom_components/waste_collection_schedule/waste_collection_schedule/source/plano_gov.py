import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# City of Plano ArcGIS "ServicedAddresses" layer, one feature per address
# (looked up by its OBJECTID). Trash is a recurring weekday (DAY_2017),
# shifted a single day forward when it lands on a US federal holiday; bulky
# and recycling are published as explicit month/day strings for the current
# and next two collections, so those need no recurrence projection at all,
# only date parsing. The holiday calendar is the framework's shared
# recurrence.us_federal_holidays() (no per-source nth-weekday-of-month code).

FEATURE_URL = (
    "https://maps.planogis.org/arcgiswad/rest/services/Sustainability/"
    "ServicedAddresses/MapServer/0"
)
OUT_FIELDS = "DAY_2017,BLKY_CURR,BLKY_NEXT1,BLKY_NEXT2,REC_CURR,REC_NEXT1,REC_NEXT2"

_TYPE_MAP = {
    "TRASH": GENERAL_WASTE,
    "RECYCLE": RECYCLABLES,
    "BULKY": BULKY_WASTE,
}

# Default number of weekly trash collections to project when daysToGenerate
# is absent, zero or invalid (matches the legacy default).
_DEFAULT_WEEKS = 3


def _where(**params: Any) -> str:
    return f"OBJECTID={params['objectId']}"


def _parse_month_day(value: str, year: int) -> datetime.date:
    """Parse a bare "Month Day" string (e.g. 'January 1'), tacking on a year."""
    return datetime.datetime.strptime(f"{value.strip()} {year}", "%B %d %Y").date()


def _bulky_dates(attrs: dict, year: int):
    for field_name in ("BLKY_CURR", "BLKY_NEXT1", "BLKY_NEXT2"):
        value = attrs.get(field_name)
        if value:
            yield _parse_month_day(value, year)


def _recycle_dates(attrs: dict, year: int):
    """Parse REC_CURR/NEXT1/NEXT2: a "Month Day[, Day[, Day]]" string, one
    collection per comma-separated day, all sharing the first day's month."""
    for field_name in ("REC_CURR", "REC_NEXT1", "REC_NEXT2"):
        value = attrs.get(field_name)
        if not value:
            continue
        parts = value.split(",")
        first = _parse_month_day(parts[0], year)
        yield first
        for extra_day in parts[1:]:
            yield datetime.datetime.strptime(
                f"{first.month} {extra_day} {year}", "%m %d %Y"
            ).date()


def _describe(attrs, source):
    today = datetime.date.today()
    weeks = source.params.get("daysToGenerate") or _DEFAULT_WEEKS

    trash_weekday = recurrence.weekday(attrs.get("DAY_2017", ""))
    if trash_weekday is not None:
        yield Schedule(
            "TRASH",
            recurrence.next_weekday(trash_weekday, on_or_after=today),
            recurrence.WEEKLY,
            weeks,
        )

    for collection_date in _bulky_dates(attrs, today.year):
        yield Schedule("BULKY", collection_date, count=1)

    for collection_date in _recycle_dates(attrs, today.year):
        yield Schedule("RECYCLE", collection_date, count=1)


def _adjust(collection_date: datetime.date, key: str, source) -> datetime.date:
    """Bump a Trash collection one day forward if it lands on a US federal
    holiday. A single bump, not a loop: the legacy source didn't check whether
    the bumped day is itself a holiday, so neither do we."""
    if key != "TRASH":
        return collection_date
    if collection_date in recurrence.us_federal_holidays(
        collection_date.year, observed=False
    ):
        return collection_date + datetime.timedelta(days=1)
    return collection_date


@final
class Source(BaseSource):
    TITLE = "City of Plano"
    DESCRIPTION = "Source script for plano.gov"
    URL = "https://www.plano.gov/630/Residential-Collection-Schedules"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "GoodObjectId3Days": {"objectId": "72866", "daysToGenerate": "3"},
        "GoodObjectId5Days": {"objectId": "72866", "daysToGenerate": "5"},
        "GoodObjectId0Days": {"objectId": "72866", "daysToGenerate": "0"},
    }

    PARAMS = (
        text_field("objectId", "Object ID"),
        text_field(
            "daysToGenerate",
            "Number of weeks to generate for trash collection",
            default="3",
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Use the Plano interactive waste map "
            "(https://www.plano.gov/630/Residential-Collection-Schedules) to "
            "search for and retrieve your object ID using browser dev tools "
            "or a capture tool like Fiddler."
        ),
    }

    retrieve = ArcGisFeatureRetriever(FEATURE_URL, where=_where, out_fields=OUT_FIELDS)
    parse = ArcGisFeatureParser()
    preprocess = Compose(RecurrenceExpander(_describe), HolidayShift(_adjust))
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, objectId: str, daysToGenerate: str | int = "3"):
        try:
            weeks = int(daysToGenerate)
        except (TypeError, ValueError):
            weeks = 0
        if weeks <= 0:
            weeks = _DEFAULT_WEEKS
        super().__init__(objectId=str(objectId).strip(), daysToGenerate=weeks)
