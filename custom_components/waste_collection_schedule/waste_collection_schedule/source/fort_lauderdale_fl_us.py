from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# City of Fort Lauderdale "My Government Services" MapServer (public, no login).
# One zone layer per service; each polygon carries the collection weekday(s)
# as Yes/No flags plus, for monthly services, which occurrence of the weekday
# in the month (WEEKONE..WEEKFOUR) applies.
MAPSERVER = "https://gis.fortlauderdale.gov/arcgis/rest/services/MyGovernmentServices/MyGovernmentServices/MapServer"

WEEKDAY_FIELDS = [
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
]
WEEK_FIELDS = ["WEEKONE", "WEEKTWO", "WEEKTHREE", "WEEKFOUR"]
OUT_FIELDS = ",".join(["SCHEDULE", *WEEKDAY_FIELDS, *WEEK_FIELDS])

LAYERS = [
    ("Trash", f"{MAPSERVER}/7", OUT_FIELDS),
    ("Recycling", f"{MAPSERVER}/8", OUT_FIELDS),
    ("Bulk Trash", f"{MAPSERVER}/9", OUT_FIELDS),
    ("Yard Waste", f"{MAPSERVER}/10", OUT_FIELDS),
]

_TYPE_MAP = {
    "Trash": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Bulk Trash": wt.BULKY_WASTE,
    "Yard Waste": wt.GARDEN_WASTE,
}

WEEKS_AHEAD = 26
MONTHS_AHEAD = 6


def _yes(attrs: dict[str, Any], field: str) -> bool:
    return str(attrs.get(field) or "").strip().lower() == "yes"


def _describe(record, source):
    """Turn a zone's weekday / week-of-month flags into Schedule descriptors.

    A ``Weekly`` zone recurs every week on each flagged weekday. Otherwise the
    WEEKONE..WEEKFOUR flags select the n-th occurrence of the weekday per month.
    """
    label, attrs = record
    weekdays = [i for i, f in enumerate(WEEKDAY_FIELDS) if _yes(attrs, f)]
    weekly = str(attrs.get("SCHEDULE") or "").strip().lower() == "weekly"
    weeks = [i + 1 for i, f in enumerate(WEEK_FIELDS) if _yes(attrs, f)]

    for weekday in weekdays:
        if weekly:
            yield Schedule(
                label, recurrence.next_weekday(weekday), recurrence.WEEKLY, WEEKS_AHEAD
            )
            continue
        for n in weeks:
            for d in recurrence.monthly_nth_weekdays(weekday, n, MONTHS_AHEAD):
                yield Schedule(label, d)


@final
class Source(BaseSource):
    TITLE = "Fort Lauderdale, FL"
    DESCRIPTION = (
        "Source for City of Fort Lauderdale, FL trash, recycling, bulk trash and "
        "yard waste collection."
    )
    URL = "https://www.fortlauderdale.gov/government/departments-i-z/public-works/operations/sanitation-operations/collection-programs"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "413 NW 15th Ave": {"address": "413 NW 15th Ave, Fort Lauderdale, FL 33311"},
        "100 N Andrews Ave": {
            "address": "100 N Andrews Ave, Fort Lauderdale, FL 33301"
        },
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full street address including city, state and ZIP code "
            "(e.g. '413 NW 15th Ave, Fort Lauderdale, FL 33311'). It is matched "
            "against the city's 'My Government Services' collection zones "
            "(https://gis.fortlauderdale.gov/MyGovernmentServices/). Holiday "
            "shifts are not reflected."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
    ]

    retrieve = ArcGisMultiFeatureRetriever(LAYERS, address="address")
    parse = ArcGisMultiFeatureParser()
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
