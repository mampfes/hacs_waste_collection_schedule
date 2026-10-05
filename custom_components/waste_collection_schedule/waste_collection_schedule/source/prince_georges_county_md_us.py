from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import WeekdayRecurrence
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# The Department of the Environment "Once-A-Week" residential collection
# layer behind the County's own "Waste Collection Services" address tool.
_TRASH_LAYER_URL = (
    "https://gisent.princegeorgescountymd.gov/gisonline/rest/services/"
    "DoE/RRD_PROP_TRASH/MapServer/0"
)

# Fields holding a weekly day of service. Wood and tree debris is always "Call
# 311 to Schedule" (on demand), so it is not projected.
_DAY_FIELDS = {
    "Trash_Day_of_Service1": "Trash",
    "Trash_Day_of_Service2": "Trash",
    "Recycle_Day_of_Service": "Recycling",
    "Bulky_Day_of_Service": "Bulky Trash",
    "Yard_Day_of_Service": "Yard Trim",
}


@final
class Source(BaseSource):
    TITLE = "Prince George's County, MD"
    DESCRIPTION = (
        "Source for Prince George's County, Maryland curbside trash, recycling, "
        "bulky trash, and yard trim collection."
    )
    URL = "https://www.princegeorgescountymd.gov/departments-offices/environment/waste-recycling/residential-collections"
    COUNTRY = "us"
    # A property the County does not collect from (a commercial address on a
    # private hauler) has no day of service.
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "6807 McCormick Rd, Upper Marlboro": {
            "address": "6807 McCormick Rd, Upper Marlboro, MD"
        },
        "2607 Haney Ave, Suitland": {"address": "2607 Haney Ave, Suitland, MD"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter the full street address including city and state.",
    }

    retrieve = ArcGisFeatureRetriever(
        _TRASH_LAYER_URL, out_fields=",".join(sorted({*_DAY_FIELDS, "Address"}))
    )
    parse = ArcGisFeatureParser(argument="address")
    preprocess = WeekdayRecurrence(day=_DAY_FIELDS)
    transform = ICSTransformer(
        type_value_map={
            "Trash": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Bulky Trash": wt.BULKY_WASTE,
            "Yard Trim": wt.GARDEN_WASTE,
        }
    )
