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
    TITLE = "Nillumbik Shire Council"
    DESCRIPTION = "Source for Nillumbik Shire Council rubbish collection."
    URL = "https://www.nillumbik.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test": {"street_address": "11 Sunnyside Crescent, WATTLE GLEN, 3096"}
    }

    PARAMS = (street_address(field="street_address"),)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    retrieve = OpenCitiesRetriever(
        domain="https://www.nillumbik.vic.gov.au",
        address="street_address",
        warm_up_url="https://www.nillumbik.vic.gov.au/Residents/Waste-and-recycling/Bin-collection/Check-my-bin-day",
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
