from typing import ClassVar, final
from urllib.parse import quote

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Landskrona - Svalövs Renhållning"
    DESCRIPTION = "Source for LSR waste collection."
    URL = "https://www.lsr.nu"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Home": {"street_address": "Saxtorpsvägen 115, Annelöv"},
        "Polisen": {"street_address": "Herrevadsgatan 11, Svalöv"},
    }

    PARAMS = (street_address("street_address"),)

    retrieve = HttpGetRetriever(
        url=lambda street_address, **_: (
            "https://minasidor.lsr.nu/api/api/external/schedule/"
            + quote(street_address)
        ),
        # A browser's Accept header makes the API answer XML.
        headers={"Accept": "application/json"},
    )
    parse = parsers.JsonParser()
    transform = JsonTransformer(
        date_key=lambda record: record["date"][:10],
        type_key="typeOfWasteDescription",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Förpackningar och tidningar": wt.RECYCLABLES,
            "Trädgårdsavfall": wt.GARDEN_WASTE,
        },
    )
