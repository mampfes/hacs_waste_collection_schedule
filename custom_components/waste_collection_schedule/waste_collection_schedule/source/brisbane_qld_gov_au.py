from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.service.WasteInfo import (
    TYPE_VALUE_MAP,
    WasteInfoEventsParser,
    WasteInfoRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Brisbane City Council"
    DESCRIPTION = "Source for Brisbane City Council rubbish collection."
    URL = "https://www.brisbane.qld.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.OTHER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Suburban Social": {
            "suburb": "Chapel Hill",
            "street_name": "Moordale St",
            "street_number": "3",
        },
        "The Scratch Bar": {
            "suburb": "Milton",
            "street_name": "Park Rd",
            "street_number": "8/1",
        },
        "Green Beacon": {
            "suburb": "Teneriffe",
            "street_name": "Helen St",
            "street_number": "26",
        },
    }

    PARAMS = (
        text_field("suburb", "Suburb"),
        street("street_name"),
        house_number("street_number"),
    )

    retrieve = WasteInfoRetriever("https://brisbane.waste-info.com.au")
    parse = WasteInfoEventsParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        description_key="name",
    )
