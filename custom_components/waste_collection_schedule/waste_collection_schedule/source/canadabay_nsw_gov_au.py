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
    TITLE = "City of Canada Bay Council"
    DESCRIPTION = "Source for City of Canada Bay Council rubbish collection."
    URL = "https://www.canadabay.nsw.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Harry's Shed": {
            "suburb": "Concord",
            "street_name": "Gipps Street",
            "street_number": "1A",
        },
        "Five Dock Library": {
            "suburb": "Five Dock",
            "street_name": "Garfield Street",
            "street_number": "4-12",
        },
        "Dazed cafe": {
            "suburb": "Mortlake",
            "street_name": "Tennyson Road",
            "street_number": "76",
        },
    }

    PARAMS = (
        text_field("suburb", "Suburb"),
        street("street_name"),
        house_number("street_number"),
    )

    retrieve = WasteInfoRetriever("https://canada-bay.waste-info.com.au")
    parse = WasteInfoEventsParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        description_key="name",
    )
