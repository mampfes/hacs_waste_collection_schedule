from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.MendixBinForm import (
    MendixBinFormParser,
    MendixBinFormRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Knowsley Council"
    DESCRIPTION = "Source for Knowsley Council."
    URL = "https://www.knowsley.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "L364AR 000040082756": {"postcode": "L364AR", "uprn": "000040082756"},
        "L34 0HZ, 40029195": {"postcode": "L34 0HZ", "uprn": 40029195},
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": "Enter your postcode and your property's UPRN (find it at https://www.findmyaddress.co.uk/).",
    }

    retrieve = MendixBinFormRetriever("https://knowsleytransaction.mendixcloud.com/")
    parse = MendixBinFormParser()
    transform = ICSTransformer(
        type_value_map={
            "Maroon": wt.GENERAL_WASTE,
            "Grey": wt.RECYCLABLES,
            "Blue": wt.GARDEN_WASTE,
            "Food": wt.FOOD_WASTE,
        },
    )
