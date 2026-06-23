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

# Baton Rouge publishes three ArcGIS feature layers (garbage, trash, recycling).
# A spatial point query against each layer returns one feature whose day-of-week
# fields ("Monday".."Sunday") are flagged "yes" on the collection day(s). The
# declarative multi-layer retriever geocodes once and runs the spatial query
# against every layer, tagging each response with a label carrying its waste
# type; _describe() reads the flagged weekdays and projects each into a weekly
# cycle. Date projection is the shared RecurrenceExpander.

BASE_URL = "https://services.arcgis.com/KYvXadMcgf0K1EzK/arcgis/rest/services/GovernmentServices_WFL1/FeatureServer"
GARBAGE_URL = f"{BASE_URL}/14"
TRASH_URL = f"{BASE_URL}/15"
RECYCLING_URL = f"{BASE_URL}/16"

# Each layer: a (waste_type label, FeatureServer URL) pair. The label is the
# legacy raw type string the layer emits (the key into _TYPE_MAP);
# ArcGisMultiFeatureRetriever carries it through to each (label, attrs) record
# so _describe() can recover the waste type without re-deriving it from the URL.
_LAYERS = [
    ("Garbage", GARBAGE_URL),
    ("Trash", TRASH_URL),
    ("Recycling", RECYCLING_URL),
]

_TYPE_MAP = {
    "Garbage": GENERAL_WASTE,
    "Trash": GENERAL_WASTE,
    "Recycling": RECYCLABLES,
}

DAY_FIELDS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _describe(record, source):
    """Project a layer's matched feature into one weekly Schedule per flagged day.

    ``record`` is the ``(label, attrs)`` pair produced by
    :class:`ArcGisMultiFeatureParser`, where ``label`` is the waste-type string
    this source tagged each layer with (the legacy ``t=`` value).
    """
    waste_type, attrs = record
    # ArcGIS may return field names in varying case (MONDAY vs Monday).
    attrs_upper = {k.upper(): v for k, v in attrs.items()}
    for day in DAY_FIELDS:
        if (attrs_upper.get(day.upper()) or "").strip().lower() == "yes":
            yield Schedule(
                waste_type,
                recurrence.next_weekday(recurrence.WEEKDAYS[day.lower()]),
                recurrence.WEEKLY,
                26,
            )


@final
class Source(BaseSource):
    TITLE = "Baton Rouge, LA"
    DESCRIPTION = "Source for Baton Rouge, LA waste collection."
    URL = "https://www.brla.gov/337/Garbage-Collection"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "City Hall (Fri, Fri, Tue/Fri)": {
            "address": "222 Saint Louis St, Baton Rouge, LA 70802"
        },
        "Mall of Louisiana (Thu, Thu, Mon/Thu)": {
            "address": "6401 Bluebonnet Boulevard, Baton Rouge, LA 70836"
        },
        "Amazon Fulfillment Center (Wed, Sat, Wed/Sat)": {
            "address": "9001 Cortana Pl, Baton Rouge, LA 70815"
        },
    }

    PARAMS = [text_field("address", "Street Address")]

    HOWTO = {
        "en": (
            "Enter your street address within Baton Rouge, LA "
            "(e.g. '222 Saint Louis St, Baton Rouge, LA 70802')."
        ),
    }

    # Declarative pipeline: geocode once, spatially query every layer, tag each
    # response with its waste-type label, then keep only layers that matched a
    # feature. _describe() projects each match into a weekly cycle per flagged day.
    retrieve = ArcGisMultiFeatureRetriever(_LAYERS, address="address")
    parse = ArcGisMultiFeatureParser()
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())
