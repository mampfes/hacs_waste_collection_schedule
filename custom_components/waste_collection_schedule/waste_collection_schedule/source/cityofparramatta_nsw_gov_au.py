import datetime
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

_ZONES_URL = "https://services6.arcgis.com/NrOjMi9LSYL3MUze/arcgis/rest/services/CoP_Garbage_Recyle_July2021/FeatureServer/0"

# A Monday of an "Area 1" recycling week; Area 2 recycles the week after.
_AREA_1_RECYCLING_MONDAY = datetime.date(2024, 1, 1)


def _describe(record, source):
    """Red and green bins weekly, yellow (recycling) fortnightly by area."""
    weekday = recurrence.weekday((record.get("DAY") or "").strip())
    if weekday is None or not (record.get("WEEK") or "").strip():
        return
    start = recurrence.next_weekday(weekday)
    recycling = _AREA_1_RECYCLING_MONDAY + datetime.timedelta(days=weekday)
    if "area 1" not in record["WEEK"].lower():
        recycling += datetime.timedelta(weeks=1)
    yield Schedule("General Waste (Red Bin)", start, recurrence.WEEKLY, 4)
    yield Schedule(
        "Recycling (Yellow Bin)", recycling, recurrence.FORTNIGHTLY, 3, anchor=True
    )
    yield Schedule("Garden Organics (Green Bin)", start, recurrence.WEEKLY, 4)


@final
class Source(BaseSource):
    TITLE = "City of Parramatta"
    DESCRIPTION = "Source script for cityofparramatta.nsw.gov.au"
    URL = "https://www.cityofparramatta.nsw.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GARDEN_WASTE, wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "126 Church Street": {"address": "126 Church Street Parramatta"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full address including the suburb. Example: "
            "`126 Church Street Parramatta`"
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        _ZONES_URL, out_fields="DAY,WEEK", result_record_count=1
    )
    parse = ArcGisFeatureParser(argument="address")
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={
            "General Waste (Red Bin)": wt.GENERAL_WASTE,
            "Recycling (Yellow Bin)": wt.RECYCLABLES,
            "Garden Organics (Green Bin)": wt.GARDEN_WASTE,
        }
    )
