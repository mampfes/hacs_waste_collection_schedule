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
    TITLE = "Redland City Council (QLD)"
    DESCRIPTION = "Source for Redland City Council (QLD) rubbish collection."
    URL = "https://www.redland.qld.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Mount Cotton": {
            "suburb": "Mount Cotton",
            "street_name": "Mount Cotton Road",
            "street_number": "1261",
        },
        "Random Redland Bay": {
            "suburb": "Redland Bay",
            "street_name": "Boundary Street",
            "street_number": "1",
        },
        "Random Victoria Point": {
            "suburb": "Victoria Point",
            "street_name": "Colburn Avenue",
            "street_number": "25",
        },
    }

    PARAMS = (
        text_field("suburb", "Suburb"),
        street("street_name"),
        house_number("street_number"),
    )

    retrieve = WasteInfoRetriever("https://redland.waste-info.com.au")
    parse = WasteInfoEventsParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        description_key="name",
    )
