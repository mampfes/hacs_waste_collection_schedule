from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import (
    Compose,
    DateFields,
    Deduplicate,
    ExplodeList,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

_parse = date_parsers.for_format("%Y-%m-%d")


@final
class Source(BaseSource):
    TITLE = "Rushmoor Borough Council"
    DESCRIPTION = "Source for rushmoor.gov.uk services for Rushmoor, UK."
    URL = "https://rushmoor.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "GU14": {"uprn": "100060551749"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.rushmoor.gov.uk/Umbraco/Api/BinLookUpWorkAround/Get",
        params=lambda uprn, **_: {"selectedAddress": uprn, "weeks": "16"},
    )
    # The next and the previous collection, each a record with a date field
    # per stream.
    parse = parsers.JsonParser()
    preprocess = Compose(
        ExplodeList("NextCollection", "PreviousCollection"),
        DateFields(
            fields={
                "RefuseCollectionBinDate": "Refuse",
                "RecyclingCollectionDate": "Recycling",
                "GardenWasteCollectionDate": "Garden Waste",
                "FoodWasteCollectionDate": "Food Waste",
                "GlassCollectionDate": "Glass",
            },
            parse_date=lambda value: _parse(value[:10]) if value else None,
        ),
        Deduplicate(),
    )
    transform = ICSTransformer(
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
            "Food Waste": wt.FOOD_WASTE,
            "Glass": wt.GLASS,
        }
    )
