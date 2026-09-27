from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "North Lincolnshire Council"
    DESCRIPTION = (
        "Source for northlincs.gov.uk services for North Lincolnshire Council, UK."
    )
    URL = "https://www.northlincs.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100050200824"},
        "Test_002": {"uprn": "100050188326"},
        "Test_003": {"uprn": 100050199446},
        "Test_004": {"uprn": 100050196285},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://m.northlincs.gov.uk/bin_collections",
        params=lambda uprn, **_: {"no_collections": 20, "uprn": uprn},
    )
    parse = parsers.JsonParser("Collections")
    transform = JsonTransformer(
        date_key=lambda record: record["CollectionDate"][:10],
        type_key="BinCodeDescription",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "General waste wheeled bin": wt.GENERAL_WASTE,
            "Plastic and cardboard wheeled bin": wt.RECYCLABLES,
            "Brown garden waste wheeled bin": wt.GARDEN_WASTE,
        },
    )
