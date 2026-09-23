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
    TITLE = "Stonnington City Council"
    DESCRIPTION = "Source for Stonnington City Council rubbish collection."
    URL = "https://www.stonnington.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "The Jam Factory": {"street_address": "500 Chapel Street, South Yarra"},
        "Malvern Library": {"street_address": "1255 High Street, Malvern"},
    }

    PARAMS = (street_address(field="street_address"),)

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.BULKY_WASTE,
    ]

    retrieve = OpenCitiesRetriever(
        domain="https://www.stonnington.vic.gov.au",
        address="street_address",
        warm_up_url="https://www.stonnington.vic.gov.au/Services/Waste-and-recycling",
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
