from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.GrandLyon import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Métropole de Lyon"
    DESCRIPTION = "Source script for data.grandlyon.com waste collection schedules"
    URL = "https://data.grandlyon.com"
    COUNTRY = "fr"
    TEST_CASES: ClassVar[dict] = {
        "Oullins centre": {"address": "1 place Roger Salengro, Oullins"},
        "Lyon 3e Garibaldi": {"address": "208 rue Garibaldi, Lyon 3e"},
        "Villeurbanne Gratte-Ciel": {
            "address": "18 rue Francis de Pressensé, Villeurbanne"
        },
    }
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Enter your street address including the city name (e.g. '1 place Roger Salengro, Oullins').",
        "fr": "Entrez votre adresse complète avec le nom de la commune (ex : '1 place Roger Salengro, Oullins').",
    }
    PARAMS = (street_address(),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Ordures Ménagères": wt.GENERAL_WASTE,
            "Collecte Sélective": wt.RECYCLABLES,
            "Déchets Alimentaires": wt.FOOD_WASTE,
        },
    )
