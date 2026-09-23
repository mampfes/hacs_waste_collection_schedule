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
    TITLE = "Whittlesea City Council"
    DESCRIPTION = "Source for Whittlesea Council (VIC) rubbish collection."
    URL = "https://www.whittlesea.vic.gov.au/My-Neighbourhood"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Whittlesea Council Office": {
            "street_address": "25 Ferres Boulevard, South Morang 3752"
        }
    }

    PARAMS = (street_address(field="street_address"),)

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GLASS,
    ]

    retrieve = OpenCitiesRetriever(
        domain="https://www.whittlesea.vic.gov.au",
        address="street_address",
        warm_up_url="https://www.whittlesea.vic.gov.au/My-Neighbourhood",
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
