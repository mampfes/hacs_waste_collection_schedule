from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.WasteInfo import (
    TYPE_VALUE_MAP,
    WasteInfoEventsParser,
    WasteInfoRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Hobsons Bay City Council"
    DESCRIPTION = "Source for Hobsons Bay City Council waste & recycling collection"
    URL = "https://www.hobsonsbay.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Civic Parade Medical Centre": {
            "street_address": "399 Queen St, Altona Meadows"
        },
        "Hecho En Mexico Altona": {"street_address": "48 Pier St, Altona"},
        "Williamstown, no comma": {"street_address": "20 Merrett Dr Williamstown"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Street number, street name and suburb as shown on the council's bin "
            "collection calendar, for example '399 Queen St, Altona Meadows'. The "
            "comma is optional."
        ),
    }

    retrieve = WasteInfoRetriever(
        "https://hobsons-bay.waste-info.com.au", street_address="street_address"
    )
    parse = WasteInfoEventsParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        description_key="name",
    )
