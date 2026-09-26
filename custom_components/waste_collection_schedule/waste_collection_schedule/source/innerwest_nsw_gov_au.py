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
    TITLE = "Inner West Council (NSW)"
    DESCRIPTION = "Source for Inner West Council (NSW) rubbish collection."
    URL = "https://www.innerwest.nsw.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Random Marrickville address": {
            "suburb": "Tempe",
            "street_name": "Princes Highway",
            "street_number": "813",
        },
        "Random Leichhardt address": {
            "suburb": "Rozelle",
            "street_name": "Darling Street",
            "street_number": "597",
        },
        "Random Ashfield address": {
            "suburb": "Summer Hill",
            "street_name": "Lackey Street",
            "street_number": "29",
        },
    }

    PARAMS = (
        text_field("suburb", "Suburb"),
        street("street_name"),
        house_number("street_number"),
    )

    # Inner West merged three councils but still keeps their three registers;
    # the first one that knows the suburb holds the property.
    retrieve = WasteInfoRetriever(
        (
            "https://leichhardt.waste-info.com.au",
            "https://marrickville.waste-info.com.au",
            "https://ashfield.waste-info.com.au",
        )
    )
    parse = WasteInfoEventsParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        description_key="name",
    )
