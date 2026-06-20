import datetime
import re

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GARDEN_WASTE, GENERAL_WASTE

# Abilene publishes trash and yard-waste collection as two separate ArcGIS
# layers. A point-in-polygon query against each layer returns:
#   * Trash_Pickup -> "Name" = e.g. "Monday/Thursday" (one or more weekly days)
#   * Yard_Waste_Pickup -> "Pickup_Time" = "Nth DAY | ... | Odd/Even Months"
# The declarative multi-layer retriever geocodes once and runs the spatial query
# against every layer; each layer's raw /query Response is tagged with a label
# carrying its waste type and the attribute field to read, so _describe() can
# project concrete dates without the source hand-rolling retrieve()/parse():
# weekly schedules for trash, and per-occurrence one-off schedules for the
# irregular monthly-parity yard-waste pattern.

TITLE = "Abilene, TX"
DESCRIPTION = "Source for Abilene, TX solid waste and yard waste collection."
URL = "https://abilenetx.gov/426/Solid-Waste-Recycling"
COUNTRY = "us"

TEST_CASES = {
    "Chimney Rock Rd (Mon/Thu trash, 4th-Monday yard)": {
        "address": "3601 Chimney Rock Rd, Abilene, TX"
    },
    "City Hall area (Tue/Fri trash)": {"address": "555 Walnut St, Abilene, TX"},
}

TRASH_URL = "https://services6.arcgis.com/iBFmWI3dYPQqS1KF/arcgis/rest/services/Trash_Pickup/FeatureServer/0"
YARD_WASTE_URL = "https://services6.arcgis.com/iBFmWI3dYPQqS1KF/arcgis/rest/services/Yard_Waste_Pickup/FeatureServer/0"

# Each layer: a (waste_type, field) label paired with the FeatureServer URL and
# the out_fields to request. The label is the waste-type string the layer emits
# (the legacy t= value) paired with the attribute field whose value drives the
# schedule. ArcGisMultiFeatureRetriever carries the label through to each
# (label, attrs) record so _describe() can recover both without re-deriving them
# from the URL.
LAYERS = [
    (("Trash", "Name"), TRASH_URL, "Name"),
    (("Yard Waste", "Pickup_Time"), YARD_WASTE_URL, "Pickup_Time"),
]

_TYPE_MAP = {
    "Trash": GENERAL_WASTE,
    "Yard Waste": GARDEN_WASTE,
}

# Number of weekly trash collections to project (matches the legacy WEEKS_AHEAD).
WEEKS_AHEAD = 26


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> datetime.date:
    """Return the nth occurrence (1-based) of weekday (0=Mon) in the given month."""
    first = datetime.date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    first_occurrence = first + datetime.timedelta(days=offset)
    return first_occurrence + datetime.timedelta(weeks=n - 1)


def _describe(record, source):
    """Project a layer's matched attribute into Schedule descriptors.

    ``record`` is the ``(label, attrs)`` pair produced by
    :class:`ArcGisMultiFeatureParser`, where ``label`` is the
    ``(waste_type, field)`` tuple this source tagged each layer with: the
    waste-type string the layer emits and the attribute field to read.
    """
    (waste_type, field), attrs = record
    value = (attrs.get(field) or "").strip()
    if not value:
        return

    if waste_type == "Trash":
        # "Name" is one or more weekdays separated by "/", each weekly.
        for part in value.split("/"):
            weekday_idx = recurrence.WEEKDAYS.get(part.strip().lower())
            if weekday_idx is None:
                continue
            yield Schedule(
                waste_type,
                recurrence.next_weekday(weekday_idx),
                recurrence.WEEKLY,
                WEEKS_AHEAD,
            )
        return

    # Yard Waste: "Nth DAY | ... | Odd/Even Months" — irregular nth-weekday of
    # months of a given parity. Each occurrence is a one-off (future-only).
    match = re.match(
        r"(\d+)(?:st|nd|rd|th)\s+(\w+)\s*\|.*?(Odd|Even)\s+Months",
        value,
        re.IGNORECASE,
    )
    if not match:
        return

    n = int(match.group(1))
    weekday_idx = recurrence.WEEKDAYS.get(match.group(2).lower())
    if weekday_idx is None:
        return
    parity = match.group(3).lower()

    today = datetime.date.today()
    for year in range(today.year, today.year + 2):
        for month in range(1, 13):
            month_is_odd = month % 2 == 1
            if parity == "odd" and not month_is_odd:
                continue
            if parity == "even" and month_is_odd:
                continue
            try:
                d = _nth_weekday_of_month(year, month, weekday_idx, n)
            except ValueError:
                continue
            if d >= today:
                yield Schedule(waste_type, d, recurrence.WEEKLY, 1)


class Source(BaseSource):
    TITLE = TITLE
    DESCRIPTION = DESCRIPTION
    URL = URL
    COUNTRY = COUNTRY
    TEST_CASES = TEST_CASES
    RAISE_ON_EMPTY = True

    PARAMS = [text_field("address", "Street Address")]

    HOWTO = {
        "en": (
            "Enter your full street address including city and state "
            "(e.g. '3601 Chimney Rock Rd, Abilene, TX')."
        ),
    }

    # Declarative pipeline: geocode once, spatially query every layer, tag each
    # response with its (waste_type, field) label, then keep only layers that
    # matched a feature. _describe() projects each match into concrete dates.
    retrieve = ArcGisMultiFeatureRetriever(LAYERS, address="address")
    parse = ArcGisMultiFeatureParser()
    preprocessor = RecurrenceExpander(_describe)
    transformer = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())
