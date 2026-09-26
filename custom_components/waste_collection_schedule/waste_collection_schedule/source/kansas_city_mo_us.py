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

# "Trash Route Boundary" layer (carries TRASHDAY). Native SR is WKID 102698;
# the server reprojects the WGS84 point returned by the geocoder automatically.
_MAPSERVER_URL = "https://mapd.kcmo.org/kcgis/rest/services/DataLayers/MapServer/35"


@final
class Source(BaseSource):
    TITLE = "Kansas City, MO"
    DESCRIPTION = "Source for Kansas City, Missouri trash and recycling collection."
    URL = "https://www.kcmo.gov/city-hall/trash"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Paseo": {"address": "4632 Paseo, Kansas City, MO 64110"},
        "Ward Parkway": {"address": "8330 Ward Parkway, Kansas City, MO"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the full street address including city and state (e.g. "
            "'4632 Paseo, Kansas City, MO 64110')."
        ),
    }

    retrieve = ArcGisFeatureRetriever(_MAPSERVER_URL, out_fields="TRASHDAY")
    parse = ArcGisFeatureParser(argument="address")
    # Trash and unlimited recycling are collected on the same weekly day.
    preprocess = WeekdayRecurrence(day="TRASHDAY", keys=("Trash", "Recycling"))
    transform = ICSTransformer(
        type_value_map={"Trash": wt.GENERAL_WASTE, "Recycling": wt.RECYCLABLES}
    )
