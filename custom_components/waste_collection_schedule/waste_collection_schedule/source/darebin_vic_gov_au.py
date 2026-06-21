import datetime
from typing import final

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service import ArcGis
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    OTHER,
    RECYCLABLES,
)

# Attribute query in two steps (address LIKE -> OBJECTID -> full record), then a
# mix of recurring schedules: weekly rubbish, fortnightly green/recycling from
# epoch-ms base dates, and a single street-sweeping date on a 6-week cycle.
# The date math moves onto the core recurrence helpers; the only source-specific
# code is the two-step retrieve and _describe.

FEATURE_URL = "https://services-ap1.arcgis.com/1WJBRkF3v1EEG5gz/arcgis/rest/services/Waste_Collection_Date3/FeatureServer/0"

_SIX_WEEKLY = datetime.timedelta(weeks=6)
_from_ms = date_parsers.from_epoch(unit="ms")

_TYPE_MAP = {
    "Rubbish": GENERAL_WASTE,
    "Green Waste": GARDEN_WASTE,
    "Recycling": RECYCLABLES,
    "Street Sweeping": OTHER,
}


def _describe(attrs, source):
    collection_day = attrs["Collection_Day"]
    weekday = recurrence.WEEKDAYS[collection_day.lower()]

    # Rubbish — weekly from the next occurrence of the collection weekday.
    yield Schedule(
        "Rubbish",
        recurrence.most_recent_weekday(weekday),
        recurrence.WEEKLY,
        52,
        anchor=True,
    )
    # Green + Recycling — fortnightly from their epoch-ms base dates.
    yield Schedule(
        "Green Waste",
        _from_ms(attrs["Green_Collection"]),
        recurrence.FORTNIGHTLY,
        26,
        anchor=True,
    )
    yield Schedule(
        "Recycling",
        _from_ms(attrs["Recycle_Collection"]),
        recurrence.FORTNIGHTLY,
        26,
        anchor=True,
    )
    # Street sweeping — the next single date on a 6-week cycle.
    yield Schedule(
        "Street Sweeping",
        _from_ms(attrs["Street_Sweeping"]),
        _SIX_WEEKLY,
        1,
        anchor=True,
    )


@final
class Source(BaseSource):
    TITLE = "City of Darebin"
    DESCRIPTION = "Source for City of Darebin waste collection."
    URL = "https://www.darebin.vic.gov.au/"
    COUNTRY = "au"

    TEST_CASES = {
        "266 Gower Street PRESTON 3072": {
            "property_location": "266 Gower Street PRESTON 3072"
        },
        "23 EDWARDES STREET RESERVOIR 3073": {
            "property_location": "23 EDWARDES STREET RESERVOIR 3073"
        },
    }

    PARAMS = [text_field("property_location", "Property Location")]

    HOWTO = {
        "en": (
            "Enter your full property location as it appears on the council site "
            "(e.g. '266 Gower Street PRESTON 3072')."
        ),
    }

    parse = ArcGis.ArcGisFeatureParser()
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, property_location: str):
        super().__init__(property_location=property_location)

    # A two-step attribute query (address LIKE -> OBJECTID -> full record) that
    # the single-call retrievers can't express, so retrieve stays custom; but the
    # lookup response goes through the shared ArcGisFeatureParser so the
    # FeatureEnvelope shape is validated and a no-match raises a clear argument
    # error rather than an IndexError.
    def retrieve(self, source):
        location = source.params["property_location"]
        lookup = ArcGis.feature_query(
            FEATURE_URL,
            where=f"EZI_ADDRESS LIKE '{location}%'",
            out_fields="EZI_ADDRESS,OBJECTID",
        )
        matches = ArcGis.ArcGisFeatureParser()(lookup, source)
        if not matches:
            raise SourceArgumentNotFound("property_location", location)
        object_id = matches[0]["OBJECTID"]

        # Step 2: fetch the full record for that OBJECTID.
        return ArcGis.feature_query(
            FEATURE_URL,
            where=f"OBJECTID={object_id}",
            out_fields=(
                "Collection_Day,Green_Collection,Recycle_Collection,Street_Sweeping"
            ),
        )
