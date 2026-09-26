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
    TITLE = "Cumberland Council (NSW)"
    DESCRIPTION = "Source for Cumberland Council (NSW) rubbish collection."
    URL = "https://www.cumberland.nsw.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Berala Community Centre": {
            "suburb": "Berala",
            "street_name": "Woodburn Road",
            "street_number": "98 to 104",
        },
        "McDonald's Auburn": {
            "suburb": "Auburn",
            "street_name": "Parramatta Road",
            "street_number": "116",
        },
        "Chickenlicious Guildford": {
            "suburb": "Guildford",
            "street_name": "Woodville Road",
            "street_number": 283,
        },
    }

    PARAMS = (
        text_field("suburb", "Suburb"),
        street("street_name"),
        house_number("street_number"),
    )

    retrieve = WasteInfoRetriever("https://cumberland.waste-info.com.au")
    parse = WasteInfoEventsParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        description_key="name",
    )
