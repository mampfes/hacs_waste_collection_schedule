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

# The Town of Huntington's "Government Services" web app is backed by a public
# parcel layer carrying the weekly collection days per property: refuse twice a
# week ("MONDAY/THURSDAY" or "TUESDAY/FRIDAY"), recycling and yard waste once.
# The layer only holds weekdays, so the dates are projected as weekly series.
LAYER_URL = "https://geo.huntingtonny.gov/arcgis/rest/services/Public/Government_Services_v2/MapServer/0"

_TYPE_MAP = {
    "Refuse": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Yard Waste": wt.GARDEN_WASTE,
}

# attribute field -> label of the waste type it carries.
_FIELDS = {
    "COLLECTION": "Refuse",
    "Recycling": "Recycling",
    "YardWaste": "Yard Waste",
}

# Number of weekly collections to project.
WEEKS_AHEAD = 26


def _describe(attrs, source):
    """Project each collection-day field of the matched parcel into weekly series."""
    for field, label in _FIELDS.items():
        for part in (attrs.get(field) or "").split("/"):
            weekday = recurrence.weekday(part.strip())
            if weekday is None:
                continue
            yield Schedule(
                label, recurrence.next_weekday(weekday), recurrence.WEEKLY, WEEKS_AHEAD
            )


@final
class Source(BaseSource):
    TITLE = "Town of Huntington, NY"
    DESCRIPTION = (
        "Source for Town of Huntington, NY refuse, recycling and yard waste collection."
    )
    URL = "https://huntingtonny.gov/trash-recycling"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "E Main St (Tue/Fri refuse)": {"address": "242 E Main St, Huntington, NY"},
        "E Main St (Mon/Thu refuse)": {"address": "141 E Main St, Huntington, NY"},
    }

    PARAMS = (street_address(),)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full street address including town and state "
            "(e.g. '242 E Main St, Huntington, NY'). Only the weekdays are "
            "published, so holiday shifts and the yard waste season are not "
            "reflected."
        ),
    }

    # Declarative pipeline: geocode the address, spatially query the parcel
    # layer, then project the matched weekdays into weekly series.
    retrieve = ArcGisFeatureRetriever(LAYER_URL, address="address")
    parse = ArcGisFeatureParser(argument="address")
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
