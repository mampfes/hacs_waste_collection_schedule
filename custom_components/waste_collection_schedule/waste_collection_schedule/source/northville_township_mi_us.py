from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# ArcGis attribute query (a LIKE clause on the street address — no geocode) ->
# one feature carrying the service weekday (New_Day). Three weekly schedules
# (garbage, recycling, compostables) are projected from that weekday. Acquisition
# + parse are the shared ArcGis components; the only source-specific code is
# _describe (read the weekday, fan out three weekly schedules).

FEATURE_URL = "https://services.arcgis.com/eKu0BIfy09ymzWZF/arcgis/rest/services/Day_change_TrashCollection/FeatureServer/0"

_TYPE_MAP = {
    "Garbage": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Compostables": wt.ORGANIC,
}

_WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
}


def _describe(attrs, source):
    service_day = (attrs.get("New_Day") or "").strip()
    if not service_day or service_day not in _WEEKDAYS:
        return

    start = recurrence.next_weekday(_WEEKDAYS[service_day])
    for waste_type in _TYPE_MAP:
        yield Schedule(waste_type, start, recurrence.WEEKLY, 26)


@final
class Source(BaseSource):
    TITLE = "Northville Township, MI"
    DESCRIPTION = "Source for Northville Township, MI waste collection."
    URL = "https://www.twp.northville.mi.us"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Northville Rd": {"address": "16795 Northville Rd"},
        "6 Mile Rd": {"address": "39715 6 Mile Rd"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter your street address (e.g. '16795 Northville Rd').",
    }

    retrieve = ArcGisFeatureRetriever(
        FEATURE_URL,
        where=lambda **p: f"propstreetcombined LIKE '{p['address'].strip().upper()}%'",
        out_fields="propstreetcombined,New_Day",
    )
    parse = ArcGisFeatureParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)
