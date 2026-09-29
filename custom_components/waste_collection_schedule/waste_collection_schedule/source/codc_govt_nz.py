from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.Environz import (
    TYPE_VALUE_MAP,
    RoutesParser,
    next_service_date_retriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Central Otago District Council"
    DESCRIPTION = (
        "Source for Central Otago District Council Rubbish & Recycling collection."
    )
    URL = "https://www.codc.govt.nz/"
    COUNTRY = "nz"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@soasmileynz"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Alexandra": {"address": "5 Campbell Street Alexandra"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the full street address as displayed in the CODC Bin App, "
            "e.g. '5 Campbell Street Alexandra'."
        ),
    }

    retrieve = next_service_date_retriever(
        "codc", "bPLjJjgubEyQ3ruJqjhFenL1SoHCTzNEVGoLY5MJpP9AAzFuj8pSzA=="
    )
    parse = RoutesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map=TYPE_VALUE_MAP,
    )
