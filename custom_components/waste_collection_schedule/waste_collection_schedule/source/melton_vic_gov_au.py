from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    TYPE_VALUE_MAP,
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Melton City Council"
    DESCRIPTION = "Source for Melton City Council rubbish collection."
    URL = "https://www.melton.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Melton": {"street_address": "1 HIGH STREET MELTON 3337"},
        "Melton South": {"street_address": "3 BRIDGE ROAD MELTON SOUTH 3338"},
        "Fraser Rise": {"street_address": "20 ASPIRE BOULEVARD FRASER RISE 3336"},
        "Cobblebank": {"street_address": "2-26 FERRIS ROAD COBBLEBANK 3338"},
    }

    PARAMS = (street_address(field="street_address"),)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = OpenCitiesRetriever(
        domain="https://www.melton.vic.gov.au",
        address="street_address",
        warm_up_url="https://www.melton.vic.gov.au/My-Area",
        headers={
            "accept": "application/json, text/javascript, */*; q=0.01",
            "x-requested-with": "XMLHttpRequest",
        },
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            **TYPE_VALUE_MAP,
        },
    )
