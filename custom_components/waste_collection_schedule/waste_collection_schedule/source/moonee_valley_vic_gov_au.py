import datetime
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

# Attribute query (address LIKE) -> one feature with a collection weekday and two
# epoch-ms start dates. General waste is weekly; recycling and FOGO are
# fortnightly from their start dates. Date math moves to the core recurrence
# helpers; the only source-specific code is the where clause and _describe.

FEATURE_URL = "https://services8.arcgis.com/Qhxu8dzT7BHYuJZL/arcgis/rest/services/BinCollection_add/FeatureServer/0"

_TYPE_MAP = {
    "General Waste": GENERAL_WASTE,
    "Recycling": RECYCLABLES,
    "FOGO": ORGANIC,
}


def _where(**params) -> str:
    search = params["property_location"].strip().replace("  ", " ")
    return f"EZI_ADDRES LIKE '{search}%'"


def _describe(attrs, source):
    collection_day = attrs.get("collectday", "")
    weekday = (
        recurrence.WEEKDAYS.get(collection_day.lower()) if collection_day else None
    )
    start = (
        recurrence.most_recent_weekday(weekday)
        if weekday is not None
        else datetime.date.today()
    )
    # General waste — weekly.
    yield Schedule("General Waste", start, recurrence.WEEKLY, 52, anchor=True)

    # Recycling + FOGO — fortnightly from their epoch-ms start dates (if present).
    recycling = attrs.get("recy_stdat")
    if recycling:
        yield Schedule(
            "Recycling",
            datetime.date.fromtimestamp(recycling / 1000),
            recurrence.FORTNIGHTLY,
            26,
            anchor=True,
        )
    fogo = attrs.get("green_st_d")
    if fogo:
        yield Schedule(
            "FOGO",
            datetime.date.fromtimestamp(fogo / 1000),
            recurrence.FORTNIGHTLY,
            26,
            anchor=True,
        )


@final
class Source(BaseSource):
    TITLE = "City of Moonee Valley"
    DESCRIPTION = "Source for City of Moonee Valley waste collection."
    URL = "https://www.mvcc.vic.gov.au/"
    COUNTRY = "au"

    TEST_CASES: ClassVar[dict] = {
        "309 Buckley St, Aberfeldie VIC 3040": {
            "property_location": "309 BUCKLEY STREET ABERFELDIE 3040"
        },
        "1/157 Military Road, Avondale Heights VIC 3034": {
            "property_location": "1/157 MILITARY ROAD AVONDALE HEIGHTS 3034"
        },
    }

    PARAMS = (text_field("property_location", "Property Location"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full property location as it appears on the council site "
            "(e.g. '309 BUCKLEY STREET ABERFELDIE 3040')."
        ),
    }

    retrieve = ArcGisFeatureRetriever(FEATURE_URL, where=_where, out_fields="*")
    parse = ArcGisFeatureParser()
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, property_location: str):
        super().__init__(property_location=property_location)
