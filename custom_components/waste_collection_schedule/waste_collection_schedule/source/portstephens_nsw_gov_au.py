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
    TITLE = "Port Stephens Council"
    DESCRIPTION = "Source for Port Stephens Council waste collection."
    URL = "https://www.portstephens.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.OTHER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "randomHouse1": {
            "suburb": "Soldiers Point",
            "street_name": "Lyndel Close",
            "street_number": "2",
        },
        "randomHouse2": {
            "suburb": "Bobs Farm",
            "street_name": "Marsh Road",
            "street_number": 322,
        },
    }

    PARAMS = (
        text_field("suburb", "Suburb"),
        street("street_name"),
        house_number("street_number"),
    )

    retrieve = WasteInfoRetriever("https://port-stephens.waste-info.com.au")
    parse = WasteInfoEventsParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        description_key="name",
    )
