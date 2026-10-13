from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.BonConseilCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Notre-Dame-du-Bon-Conseil (Village)"
    DESCRIPTION = "Source for villagebonconseil.ca waste collection calendar"
    URL = "https://villagebonconseil.ca"
    COUNTRY = "ca"
    TEST_CASES: ClassVar[dict] = {"Village": {}}
    PARAMS = ()

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Ordures ménagères": wt.GENERAL_WASTE,
            "Matières organiques": wt.ORGANIC,
            "Matières recyclables": wt.RECYCLABLES,
            "Conteneur en métal – Déchets": wt.GENERAL_WASTE,
            "Conteneur en métal – Recyclage": wt.RECYCLABLES,
            "Encombrants": wt.BULKY_WASTE,
        },
    )
