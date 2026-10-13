from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.service.GrandBesancon import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Grand Besançon Métropole"
    DESCRIPTION = (
        "Source for waste collection schedules in Grand Besançon Métropole, France."
    )
    URL = "https://www.grandbesancon.fr"
    COUNTRY = "fr"
    TEST_CASES: ClassVar[dict] = {
        "Amagney, Rue de Besancon 1": {
            "insee_code": "25014",
            "street": "Rue de Besancon",
            "house_number": "1",
        },
        "Besançon, chemin de la barre aux chevaux 1": {
            "insee_code": "25056",
            "street": "chemin de la barre aux chevaux",
            "house_number": "1",
        },
    }
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Find your commune's INSEE code at https://www.insee.fr. Enter your street name as shown on the Grand Besançon waste calendar at https://data.grandbesancon.fr/opendata/dataset/joursDeCollecteDechets.",
        "fr": "Trouvez le code INSEE de votre commune sur https://www.insee.fr. Entrez le nom de votre rue tel qu'affiché sur le calendrier des déchets de Grand Besançon à https://data.grandbesancon.fr/opendata/dataset/joursDeCollecteDechets.",
    }
    PARAMS = (
        text_field("insee_code", "INSEE Code", coerce=lambda value: str(value).strip()),
        street(),
        house_number(optional=True),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Ordures ménagères": wt.GENERAL_WASTE,
            "Tri sélectif": wt.RECYCLABLES,
        },
    )
