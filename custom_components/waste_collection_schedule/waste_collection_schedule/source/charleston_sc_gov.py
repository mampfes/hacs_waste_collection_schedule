from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import WeekdayRecurrence
from waste_collection_schedule.service.ArcGis import (
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_MAP_SERVER = "https://gis.charleston-sc.gov/arcgis2/rest/services/External/mapnetExternal/MapServer"

# Garbage and trash/yard-waste are collected on independent routes and can
# fall on different weekdays for the same address, so each layer is its own
# stream. Not every address falls inside every route layer.
_LAYERS = [
    ("Garbage", f"{_MAP_SERVER}/10", "DAY"),
    ("Trash & Yard Waste", f"{_MAP_SERVER}/11", "DAY"),
]


@final
class Source(BaseSource):
    TITLE = "Charleston, SC"
    DESCRIPTION = (
        "Source for City of Charleston, SC garbage and trash/yard-waste collection."
    )
    URL = "https://www.charleston-sc.gov/345/Environmental-Services"
    COUNTRY = "us"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@dmkjr"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GARDEN_WASTE, wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Downtown Charleston": {"address": "123 Coming St, Charleston, SC 29403"},
        "Johns Island (Trident Waste)": {
            "address": "2758 August Rd, Johns Island, SC 29455"
        },
        "Daniel Island (Berkeley County)": {
            "address": "1865 Pierce St, Charleston, SC 29492"
        },
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter the full street address including city, state, and ZIP code.",
    }

    retrieve = ArcGisMultiFeatureRetriever(_LAYERS)
    parse = ArcGisMultiFeatureParser()
    preprocess = WeekdayRecurrence(
        day=lambda record: record[1].get("DAY"), keys=lambda record: record[0]
    )
    transform = ICSTransformer(
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Trash & Yard Waste": wt.GARDEN_WASTE,
        },
        carry_raw_label=True,
    )
