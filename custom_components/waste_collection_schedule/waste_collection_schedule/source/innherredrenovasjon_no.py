from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import Compose, ExplodeList, FlattenGroups
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Innherred Renovasjon"
    DESCRIPTION = (
        "Source for innherredrenovasjon.no services for Innherred Renovasjon, Norway."
    )
    URL = "https://innherredrenovasjon.no/"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"address": "Gevingåsen 206"},
        "Test_002": {"address": "Bollgardssletta 211 A"},
        "Test_003": {"address": "Nordregata 2"},
    }

    PARAMS = (street_address(),)

    retrieve = HttpGetRetriever(
        url="https://innherredrenovasjon.no/wp-json/ir/v1/garbage-disposal-dates-by-address",
        params=lambda address, **_: {"address": address},
    )
    # Fractions keyed by id, each listing its dates.
    parse = parsers.JsonParser()
    preprocess = Compose(FlattenGroups(), ExplodeList("dates", into="date"))
    transform = JsonTransformer(
        date_key=lambda record: record["date"][:10],
        type_key="fraction_name",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Matavfall": wt.FOOD_WASTE,
            "Plastemballasje": wt.RECYCLABLES,
            "Restavfall": wt.GENERAL_WASTE,
            "Restavfall mini": wt.GENERAL_WASTE,
            "Papp/papir": wt.PAPER,
            "Papir": wt.PAPER,
            "Glass- og metallemballasje": wt.GLASS,
        },
    )
