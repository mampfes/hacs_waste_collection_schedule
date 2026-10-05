from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import (
    Compose,
    DateFields,
    DefaultPreprocessor,
)
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import ICSTransformer

_parse = date_parsers.for_format("%Y-%m-%d")


@final
class Source(BaseSource):
    TITLE = "Wealden District Council"
    DESCRIPTION = "Source for Wealden City services for Wealden District Council, UK."
    URL = "https://www.wealden.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "10094620272"},
        "Test_002": {"uprn": "200001678582"},
        "Test_003": {"uprn": 100060120819},
        "Test_004": {"uprn": 100060122306},
    }

    PARAMS = (uprn(),)

    retrieve = HttpPostRetriever(
        url="https://www.wealden.gov.uk/wp-admin/admin-ajax.php",
        data=lambda uprn, **_: {
            "action": "wealden_get_collections_for_uprn",
            "uprn": uprn,
        },
    )
    # One record, a date field per stream; a stream the property does not
    # have is an empty string.
    parse = parsers.JsonParser("collection")
    preprocess = Compose(
        DefaultPreprocessor(),
        DateFields(
            fields={
                "refuseCollectionDate": "Rubbish",
                "recyclingCollectionDate": "Recycling",
                "gardenCollectionDate": "Garden",
                "foodCollectionDate": "Food",
            },
            parse_date=lambda value: _parse(value[:10]) if value else None,
        ),
    )
    transform = ICSTransformer(
        type_value_map={
            "Rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden": wt.GARDEN_WASTE,
            "Food": wt.FOOD_WASTE,
        }
    )
