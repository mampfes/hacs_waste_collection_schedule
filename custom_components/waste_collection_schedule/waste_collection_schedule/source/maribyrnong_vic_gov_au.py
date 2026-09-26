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
    TITLE = "Maribyrnong Council"
    DESCRIPTION = "Source for Maribyrnong Council (VIC) rubbish collection."
    URL = "https://www.maribyrnong.vic.gov.au/Residents/Bins-and-recycling"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Random address": {
            "suburb": "Footscray",
            "street_name": "Ballarat Rd",
            "street_number": "70-100",
        }
    }

    PARAMS = (
        text_field("suburb", "Suburb"),
        street("street_name"),
        house_number("street_number"),
    )

    retrieve = WasteInfoRetriever("https://maribyrnong.waste-info.com.au")
    parse = WasteInfoEventsParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        description_key="name",
    )
