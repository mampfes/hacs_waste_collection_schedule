from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, municipality, street
from waste_collection_schedule.service.MontpellierCollectionReference import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Montpellier Méditerranée Métropole"
    DESCRIPTION = "Source for waste collection schedules in Montpellier Méditerranée Métropole, France."
    URL = "https://data.montpellier3m.fr"
    COUNTRY = "fr"
    TEST_CASES: ClassVar[dict] = {
        "Montpellier, Rue Parlier 3": {
            "street_name": "Rue Parlier",
            "house_number": 3,
            "commune": "MONTPELLIER",
        },
        "Montpellier, Rue Parlier 8": {
            "street_name": "Rue Parlier",
            "house_number": 8,
            "commune": "MONTPELLIER",
        },
        "Lattes, Avenue de Montpellier": {
            "street_name": "Avenue de Montpellier",
            "commune": "LATTES",
        },
        "Castelnau-le-Lez, Chemin des Alouettes": {
            "street_name": "Chemin des Alouettes",
            "commune": "CASTELNAU-LE-LEZ",
        },
    }
    PARAMS = (
        street("street_name"),
        house_number(optional=True),
        municipality("commune", optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Ordures ménagères": wt.GENERAL_WASTE,
            "Tri sélectif": wt.RECYCLABLES,
            "Biodéchets": wt.ORGANIC,
            "Encombrants": wt.BULKY_WASTE,
        },
    )
