import datetime

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

# Albany publishes its collection zones as four separate ArcGIS layers
# (General/Recycling x Zone A/B). The point-in-polygon query against each layer
# tells us which weekday that layer collects on (a "<weekday>": "YES" attribute),
# and each layer carries a historical Monday anchor that pins its fortnightly
# cycle. The declarative multi-layer retriever geocodes once and runs the spatial
# query against every layer; each layer's raw /query Response is tagged with a
# label carrying its waste type and anchor, so _describe() can project the
# fortnightly dates without the source hand-rolling retrieve()/parse().

_TYPE_MAP = {
    "General Waste & FOGO": GENERAL_WASTE,
    "Recycling": RECYCLABLES,
}

# Each layer: the FeatureServer URL plus a (waste_type, anchor) label. The label
# is the waste-type string the layer emits (the legacy t= value) paired with the
# historical Monday anchor for its fortnightly cycle. ArcGisMultiFeatureRetriever
# carries the label through to each (label, attrs) record so _describe() can
# recover both without re-deriving them from the URL.
LAYERS = [
    (
        ("General Waste & FOGO", datetime.date(2021, 6, 28)),
        "https://services6.arcgis.com/qG6LEFhXeMyvh3U3/arcgis/rest/services/Trash_Pickup_A/FeatureServer/0",
    ),
    (
        ("General Waste & FOGO", datetime.date(2021, 6, 21)),
        "https://services6.arcgis.com/qG6LEFhXeMyvh3U3/arcgis/rest/services/Trash_Pickup_B/FeatureServer/0",
    ),
    (
        ("Recycling", datetime.date(2021, 6, 21)),
        "https://services6.arcgis.com/qG6LEFhXeMyvh3U3/arcgis/rest/services/Recycling_Pickup_A/FeatureServer/0",
    ),
    (
        ("Recycling", datetime.date(2021, 6, 28)),
        "https://services6.arcgis.com/qG6LEFhXeMyvh3U3/arcgis/rest/services/Recycling_Pickup_B/FeatureServer/0",
    ),
]

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
}


def _describe(record, source):
    """Project a layer's matched feature into one fortnightly Schedule.

    ``record`` is the ``(label, attrs)`` pair produced by
    :class:`ArcGisMultiFeatureParser`, where ``label`` is the
    ``(waste_type, anchor)`` tuple this source tagged each layer with.
    """
    (waste_type, anchor), attrs = record

    day_name = next(
        (k for k in _WEEKDAYS if str(attrs.get(k, "")).upper() == "YES"),
        None,
    )
    if day_name is None:
        return

    day_of_week = _WEEKDAYS[day_name]
    # Anchor the cycle to the requested weekday within the anchor's Monday-week,
    # then roll forward to the first occurrence on/after today (anchor=True).
    week_monday = anchor - datetime.timedelta(days=anchor.weekday())
    start = week_monday + datetime.timedelta(days=day_of_week)
    yield Schedule(waste_type, start, recurrence.FORTNIGHTLY, 13, anchor=True)


class Source(BaseSource):
    TITLE = "City of Albany"
    DESCRIPTION = "Source for City of Albany, Western Australia waste collection."
    URL = "https://www.albany.wa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Laithwood Circuit Marbelup (Zone A)": {
            "address": "Laithwood Circuit, Marbelup, Albany WA 6330"
        },
        "15 Melville Street Albany (Zone B)": {
            "address": "15 Melville Street, Albany WA 6330"
        },
    }

    PARAMS = [text_field("address", "Street Address")]

    HOWTO = {
        "en": (
            "Enter your street address within the City of Albany "
            "(e.g. '15 Melville Street, Albany WA 6330')."
        ),
    }

    # Declarative pipeline: geocode once, spatially query every layer, tag each
    # response with its (waste_type, anchor) label, then keep only layers that
    # matched a feature. _describe() projects each match into a fortnightly cycle.
    retrieve = ArcGisMultiFeatureRetriever(LAYERS, address="address")
    parse = ArcGisMultiFeatureParser()
    preprocessor = RecurrenceExpander(_describe)
    transformer = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())
