from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Ökrab Sophämntning"
    DESCRIPTION = "Source script for Ökrab waste collection."
    URL = "https://okrab.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Skolan": {"address": "SKOLGATAN 1, S:T OLOF"},
        "Butiken": {"address": "KILLEBACKEN 6, KIVIK"},
    }

    PARAMS = (street_address(),)

    retrieve = HttpPostRetriever(
        url="https://minasidor.okrab.se/MinaSidor_API/api/external/schedulePost/",
        data=lambda address, **_: {"Address": address},
        # A browser's Accept header makes the API answer XML.
        headers={"Accept": "application/json"},
    )
    parse = parsers.JsonParser()
    transform = JsonTransformer(
        date_key=lambda record: record["date"][:10],
        type_key="typeOfWasteDescription",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Hushållsavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Plastförpackningar": wt.RECYCLABLES,
            "Metallförpackningar": wt.RECYCLABLES,
            "Tidningar": wt.PAPER,
            "Pappersförpackningar": wt.PAPER,
            "Färgat glas": wt.GLASS,
            "Ofärgat glas": wt.GLASS,
        },
    )
