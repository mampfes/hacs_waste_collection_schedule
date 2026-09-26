from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.BbdWhitespace import (
    PARSE_DATE,
    TYPE_VALUE_MAP,
    CollectionDatesParser,
    collection_dates_retriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Erewash Borough Council"
    DESCRIPTION = "Source for erewash.gov.uk services for Erewash Borough Council, UK."
    URL = "https://www.erewash.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100030126659"},
        "Test_002": {"uprn": "100030154311"},
        "Test_003": {"uprn": "100030118783"},
    }

    PARAMS = (uprn(),)

    retrieve = collection_dates_retriever("https://www.erewash.gov.uk")
    parse = CollectionDatesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="service",
        parse_date=PARSE_DATE,
        type_value_map=TYPE_VALUE_MAP,
    )
