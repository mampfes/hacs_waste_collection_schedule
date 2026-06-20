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

# ArcGis single spatial query -> one feature with a "Trashday" string such as
# "Monday / Thursday". Each named day projects a weekly garbage schedule.
# Acquisition + parse are the shared ArcGis components; the only source-specific
# code is _describe (splitting Trashday into weekly schedules).

FEATURE_URL = "https://services8.arcgis.com/LmhR4UJYxC4YhccG/arcgis/rest/services/Hoover_Garbage_Pickup_WFL1/FeatureServer/2"

_TYPE_MAP = {
    "Garbage": GENERAL_WASTE,
}


def _describe(attrs, source):
    trashday = (attrs.get("Trashday") or "").strip()
    if not trashday:
        return

    for part in trashday.split("/"):
        day = part.strip().lower()
        if day in recurrence.WEEKDAYS:
            yield Schedule(
                "Garbage",
                recurrence.next_weekday(recurrence.WEEKDAYS[day]),
                recurrence.WEEKLY,
                26,
            )


class Source(BaseSource):
    TITLE = "Hoover, AL"
    DESCRIPTION = "Source for Hoover, AL garbage collection."
    URL = "https://hooveralabama.gov"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Tyler Rd (Mon/Thu)": {"address": "2255 Tyler Rd, Hoover, AL"},
        "Cobblestone Ln (Tue/Fri)": {"address": "101 Cobblestone Ln, Hoover, AL"},
    }

    PARAMS = [text_field("address", "Street Address")]

    HOWTO = {
        "en": (
            "Enter your street address within Hoover, AL "
            "(e.g. '2255 Tyler Rd, Hoover, AL')."
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        FEATURE_URL, address="address", out_fields="Trashday"
    )
    parse = ArcGisFeatureParser()
    preprocessor = RecurrenceExpander(_describe)

    transformer = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
