from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.SitevisionFetchPlanner import (
    FetchPlannerParser,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Falu Energi & Vatten (FEV)"
    DESCRIPTION = (
        "Source for Falu Energi & Vatten waste collection schedule, Falun, Sweden."
    )
    URL = "https://fev.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.PLASTIC,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rådmansvägen 3": {"address": "Rådmansvägen 3"},
        "Rådmansvägen 5": {"address": "Rådmansvägen 5"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to https://fev.se/atervinning/sophamtning.html, search for your "
            "address and copy the street name and house number exactly as shown "
            "in the results, e.g. `Rådmansvägen 3`. The website only publishes "
            "the next two collections per waste type, so the interval between "
            "them is used to project further collections; shifts around "
            "holidays appear only once the website itself shows them."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(
        url="https://fev.se/atervinning/sophamtning.html",
        params=lambda address, **_: {"q": address},
    )
    parse = FetchPlannerParser(argument="address", count=12)
    transform = RowTransformer(
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Trädgårdsavfall": wt.GARDEN_WASTE,
            "Plastförpackningar": wt.PLASTIC,
            "Pappersförpackningar": wt.PAPER,
        },
    )
