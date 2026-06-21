import datetime
import re
from typing import final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

# Rochester publishes trash and recycling as two separate ArcGIS layers on one
# MapServer. A point-in-polygon query against each layer returns the collection
# day. Trash is weekly (the matched feature flags a "<Weekday>": "Yes"
# attribute); recycling is fortnightly, anchored to the date embedded in its
# NEXTPICKUP text (falling back to a weekly day field when that text is absent).
# The declarative multi-layer retriever geocodes once and runs the spatial query
# against every layer; each layer's raw /query Response is tagged with a label
# carrying its (waste_type, cadence), and each layer requests its own out_fields,
# so _describe() can reproduce the projection without hand-rolling retrieve().

BASE_URL = "http://maps.cityofrochester.gov/arcgis/rest/services/App_CityServices/City_Services/MapServer"
TRASH_URL = f"{BASE_URL}/8"
RECYCLING_URL = f"{BASE_URL}/9"

DAY_FIELDS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

_TYPE_MAP = {
    "Trash": GENERAL_WASTE,
    "Recycling": RECYCLABLES,
}

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

# Regex to extract month and day from NEXTPICKUP/TRASHPICKUPIS fields
# e.g. "in two weeks on Wednesday, April 22</a>"
DATE_RE = re.compile(r"(?P<month>" + "|".join(MONTHS.keys()) + r")\s+(?P<day>\d{1,2})")

# Each layer is declared as (label, url, out_fields) for the multi-layer
# retriever. The label is the (waste_type, cadence) pair the layer emits — the
# waste_type is the legacy t= value and the cadence drives how _describe()
# projects the dates. out_fields requests exactly the legacy field set per layer
# (day flags for weekly trash; NEXTPICKUP + DOW + day flags for fortnightly
# recycling). ArcGisMultiFeatureRetriever carries the label through to each
# (label, attrs) record so _describe() recovers both without re-deriving them.
LAYERS = [
    (("Trash", "weekly"), TRASH_URL, ",".join(DAY_FIELDS)),
    (
        ("Recycling", "fortnightly"),
        RECYCLING_URL,
        "NEXTPICKUP,DOW," + ",".join(DAY_FIELDS),
    ),
]


def _collection_day(attrs: dict) -> str | None:
    """Return the first day-field flagged 'yes' (case-insensitive)."""
    attrs_upper = {k.upper(): v for k, v in attrs.items()}
    for day in DAY_FIELDS:
        if (attrs_upper.get(day.upper()) or "").strip().lower() == "yes":
            return day
    return None


def _parse_next_date(text: str) -> datetime.date | None:
    """Extract a base date from a NEXTPICKUP text snippet (or None)."""
    if not text:
        return None
    match = DATE_RE.search(text)
    if not match:
        return None
    month = MONTHS[match.group("month")]
    day = int(match.group("day"))
    today = datetime.datetime.now().date()
    # Assume current year, but if the date is far in the past, use next year.
    year = today.year
    try:
        result = datetime.date(year, month, day)
    except ValueError:
        return None
    if result < today - datetime.timedelta(days=60):
        result = datetime.date(year + 1, month, day)
    return result


def _describe(record, source):
    """Project a layer's matched feature into its recurring Schedule(s).

    ``record`` is the ``(label, attrs)`` pair produced by
    :class:`ArcGisMultiFeatureParser`, where ``label`` is the
    ``(waste_type, cadence)`` tuple this source tagged each layer with.
    """
    (waste_type, cadence), attrs = record

    if cadence == "weekly":
        day = _collection_day(attrs)
        weekday = recurrence.weekday(day) if day else None
        if weekday is not None:
            yield Schedule(
                waste_type,
                recurrence.next_weekday(weekday),
                recurrence.WEEKLY,
                26,
            )
        return

    # Fortnightly recycling: prefer the NEXTPICKUP anchor date, else fall back to
    # a weekly day field (DOW or the "<Weekday>": "Yes" flags).
    base = _parse_next_date(attrs.get("NEXTPICKUP", ""))
    if base:
        yield Schedule(waste_type, base, recurrence.FORTNIGHTLY, 13)
        return

    day = (attrs.get("DOW", "") or "").strip() or _collection_day(attrs)
    weekday = recurrence.weekday(day) if day else None
    if weekday is not None:
        yield Schedule(
            waste_type, recurrence.next_weekday(weekday), recurrence.WEEKLY, 26
        )


@final
class Source(BaseSource):
    TITLE = "Rochester, NY"
    DESCRIPTION = "Source for Rochester, NY waste collection."
    URL = "https://www.cityofrochester.gov"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Parsells Ave (Wed/A)": {"address": "124 Parsells Ave, Rochester, NY"},
        "Lyell Ave (Mon/B)": {"address": "200 Lyell Ave, Rochester, NY"},
    }

    PARAMS = [text_field("address", "Street Address")]

    HOWTO = {
        "en": (
            "Enter your street address within the City of Rochester "
            "(e.g. '124 Parsells Ave, Rochester, NY')."
        ),
    }

    # Declarative pipeline: geocode once, spatially query both layers, tag each
    # response with its (waste_type, cadence) label and per-layer out_fields,
    # then keep only layers that matched a feature. _describe() projects each
    # match into its weekly or fortnightly cycle.
    retrieve = ArcGisMultiFeatureRetriever(LAYERS, address="address")
    parse = ArcGisMultiFeatureParser()
    preprocessor = RecurrenceExpander(_describe)
    transformer = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())
