from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, street
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    RowFilter,
)
from waste_collection_schedule.service.SivomCalendar import (
    CalendarParser,
    calendar_retriever,
    in_season,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "SIVOM de la Vallée de l'Yerres et des Sénarts"
    DESCRIPTION = "Source for waste collection schedules from the SIVOM de la Vallée de l'Yerres et des Sénarts (sivom.com)."
    URL = "https://www.sivom.com"
    COUNTRY = "fr"
    TEST_CASES: ClassVar[dict] = {
        "Villecresnes": {"commune": "VILLECRESNES", "street": "ACACIAS Allée des"},
        "Brunoy": {"commune": "BRUNOY", "street": "ABBAYE rue de l"},
        "Yerres": {"commune": "YERRES", "street": "ABBAYE avenue de l'"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "Go to https://www.sivom.com/mesjoursdecollectes/?v=YOUR_COMMUNE to find your commune name and street name.",
        "fr": "Allez sur https://www.sivom.com/mesjoursdecollectes/?v=VOTRE_COMMUNE pour trouver le nom de votre commune et de votre rue.",
    }
    PARAMS = (
        municipality("commune"),
        street(),
    )

    retrieve = calendar_retriever
    parse = CalendarParser()
    preprocess = Compose(
        RecurrenceExpander(lambda schedule, _: (schedule,)),
        RowFilter(in_season),
    )
    transform = RowTransformer(
        type_value_map={
            "Bac vert (Résiduels)": wt.GENERAL_WASTE,
            "Bac jaune (Emballages)": wt.RECYCLABLES,
            "Bac marron (Végétaux)": wt.GARDEN_WASTE,
        },
    )
