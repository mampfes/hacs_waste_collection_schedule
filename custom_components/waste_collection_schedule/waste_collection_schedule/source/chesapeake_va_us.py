from typing import final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE

# ArcGis single spatial query -> one feature with PICKUP_DAY, from which a single
# weekly trash schedule is projected. Acquisition + parse are the shared ArcGis
# components; the only source-specific code is _describe (the pickup-day logic).

FEATURE_URL = "https://gis.cityofchesapeake.net/mapping/rest/services/WasteManagement/Trash_Collection_Areas/MapServer/0"

_TYPE_MAP = {
    "Trash": GENERAL_WASTE,
}


def _describe(attrs, source):
    pickup_day = (attrs.get("PICKUP_DAY") or "").strip().title()
    weekday = recurrence.weekday(pickup_day) if pickup_day else None
    if weekday is None:
        return

    # Trash — weekly on the area's pickup day.
    yield Schedule(
        "Trash",
        recurrence.next_weekday(weekday),
        recurrence.WEEKLY,
        26,
    )


@final
class Source(BaseSource):
    TITLE = "Chesapeake, VA"
    DESCRIPTION = "Source for Chesapeake, VA trash collection."
    URL = "https://www.cityofchesapeake.net"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "460 Sawyers Mill Xing": {
            "address": "460 Sawyers Mill Xing, Chesapeake, VA 23323"
        },
    }

    PARAMS = [text_field("address", "Street Address")]

    HOWTO = {
        "en": (
            "Enter your full street address including city and state "
            "(e.g. '460 Sawyers Mill Xing, Chesapeake, VA 23323')."
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        FEATURE_URL, address="address", out_fields="PICKUP_DAY"
    )
    parse = ArcGisFeatureParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
