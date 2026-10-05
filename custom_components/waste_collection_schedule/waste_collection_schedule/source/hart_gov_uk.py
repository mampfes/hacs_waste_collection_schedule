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
    TITLE = "Hart District Council"
    DESCRIPTION = "Source for hart.gov.uk services for Hart District Council, UK."
    URL = "https://www.hart.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100060420702"},
        "Test_002": {"uprn": "100061994826"},
        "Test_003": {"uprn": "200003085501"},
        "Test_004": {"uprn": "100062464806"},
    }

    PARAMS = (uprn(),)

    retrieve = collection_dates_retriever("https://www.hart.gov.uk")
    parse = CollectionDatesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="service",
        parse_date=PARSE_DATE,
        type_value_map=TYPE_VALUE_MAP,
    )
