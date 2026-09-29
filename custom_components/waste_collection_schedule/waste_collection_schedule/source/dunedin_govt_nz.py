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
    TITLE = "Dunedin District Council"
    DESCRIPTION = "Source for Dunedin District Council Rubbish & Recycling collection."
    URL = "https://www.dunedin.govt.nz/"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Calendar 1": {"address": "5 Bennett Road Ocean View"},
        "Calendar 2": {"address": "2 Council Street Dunedin"},
        "Collection 'c'": {"address": "2 - 90 Harbour Terrace Dunedin"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the full street address as displayed in the DCC Kerbside "
            "Collection app, e.g. '5 Bennett Road Ocean View'."
        ),
    }

    retrieve = next_service_date_retriever(
        "dcc", "F9qPiSASucQZRqKi92rttnnfZ4d8cZNh8RfTVSpQ2it2AzFuMu13mA=="
    )
    parse = RoutesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map=TYPE_VALUE_MAP,
    )
