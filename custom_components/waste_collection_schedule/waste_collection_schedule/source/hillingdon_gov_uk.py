from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.HillingdonBinDay import (
    BinDayParser,
    BinDayRetriever,
    WeeklyCollections,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "London Borough of Hillingdon"
    DESCRIPTION = "Source for London Borough of Hillingdon, UK."
    URL = "https://www.hillingdon.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Property with garden waste subscription, UB10 (Wednesday)": {
            "uprn": "100021484600"
        },
        "Property with food waste, UB10 (Wednesday)": {"uprn": "100021484628"},
        "Property with residual waste suffix, UB10 (Tuesday)": {"uprn": "100021484620"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You need your Unique Property Reference Number (UPRN). An easy "
            "way to find it is by going to https://www.findmyaddress.co.uk/ "
            "and entering your address details."
        ),
    }

    retrieve = BinDayRetriever()
    parse = BinDayParser()
    preprocess = WeeklyCollections(weeks=8)

    transform = RowTransformer(
        type_value_map={
            "Dry mixed recycling": wt.RECYCLABLES,
            "Household waste": wt.GENERAL_WASTE,
            "Residual household waste": wt.GENERAL_WASTE,
            "Trade sacks general waste": wt.GENERAL_WASTE,
            "Garden waste": wt.GARDEN_WASTE,
            "Food waste": wt.FOOD_WASTE,
        },
    )
