from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
    epoch_ms_to_date,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# City of Alexandria alx311Info MapServer, three independent zone layers:
# layer 3 = Refuse Day Zone (DAYSERVED, weekly; every serviced address has
# one), layer 2 = Recycle Zones (PICKUPDAY, weekly; not every address is
# eligible), layer 16 = Leaf Zones (PassDate, one feature per seasonal
# vacuum-leaf pass with an explicit date, only populated in season). One
# geocode, then a spatial query against all three layers via the shared
# multi-layer retriever; the only source-specific code is _describe(), which
# reads each layer's field and picks weekly-recurring vs. one-off projection.

MAPSERVER = "https://maps.alexandriava.gov/alexmaps/rest/services/alx311Info/MapServer"

# label -> (feature_url, out_fields) for the multi-layer retriever.
LAYERS = [
    ("Trash", f"{MAPSERVER}/3", "DAYSERVED"),
    ("Recycling", f"{MAPSERVER}/2", "PICKUPDAY"),
    ("Leaf Collection", f"{MAPSERVER}/16", "PassDate"),
]

# label -> attribute field _describe() reads from that layer's feature.
_FIELDS = {
    "Trash": "DAYSERVED",
    "Recycling": "PICKUPDAY",
    "Leaf Collection": "PassDate",
}

_TYPE_MAP = {
    "Trash": GENERAL_WASTE,
    "Recycling": RECYCLABLES,
    "Leaf Collection": GARDEN_WASTE,
}

# Number of weekly collections to project (matches the legacy WEEKS_AHEAD).
WEEKS_AHEAD = 26


def _describe(record, source):
    """Project a layer's matched feature into its Schedule descriptor(s).

    ``record`` is the ``(label, attrs)`` pair produced by
    :class:`ArcGisMultiFeatureParser`. Trash and Recycling carry a collection
    weekday and recur weekly; Leaf Collection carries an explicit one-off
    pass date (the layer only holds the current season, so a mismatched
    address simply yields nothing outside that window, as before).
    """
    label, attrs = record
    if label == "Leaf Collection":
        pass_date = attrs.get("PassDate")
        if pass_date:
            yield Schedule(label, epoch_ms_to_date(pass_date))
        return

    weekday = recurrence.weekday(attrs.get(_FIELDS[label], ""))
    if weekday is None:
        return
    yield Schedule(
        label, recurrence.next_weekday(weekday), recurrence.WEEKLY, WEEKS_AHEAD
    )


@final
class Source(BaseSource):
    TITLE = "Alexandria, VA"
    DESCRIPTION = (
        "Source for City of Alexandria, VA trash, recycling and leaf collection."
    )
    URL = "https://www.alexandriava.gov/RefuseCollection"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@lpukatch"]

    TEST_CASES: ClassVar[dict] = {
        "City Hall, 301 King St": {"address": "301 King St, Alexandria, VA 22314"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full street address including city and state "
            "(e.g. '301 King St, Alexandria, VA 22314')."
        ),
    }

    # Declarative pipeline: geocode once, spatially query every layer, tag
    # each response with its label, then keep only layers that matched a
    # feature. _describe() projects each match into concrete dates.
    retrieve = ArcGisMultiFeatureRetriever(LAYERS, address="address")
    parse = ArcGisMultiFeatureParser()
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())
