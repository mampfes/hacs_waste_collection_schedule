from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.WasteInfo import (
    TYPE_VALUE_MAP,
    WasteInfoEventsParser,
    WasteInfoRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Wollongong City Council"
    DESCRIPTION = "Source script for wollongongwaste.com.au"
    URL = "https://wollongongwaste.com"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {"TestName1": {"propertyID": "21444"}}

    PARAMS = (text_field("propertyID", "Property ID"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open the Waste Calendar at https://www.wollongongwaste.com.au/calendar/ "
            "with your browser's developer tools on the Network tab and look up "
            "your address. The last request is for '<propertyID>.json', e.g. "
            "https://wollongong.waste-info.com.au/api/v1/properties/21444.json"
        ),
    }

    retrieve = WasteInfoRetriever(
        "https://wollongong.waste-info.com.au", property_id="propertyID"
    )
    parse = WasteInfoEventsParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        description_key="name",
    )
