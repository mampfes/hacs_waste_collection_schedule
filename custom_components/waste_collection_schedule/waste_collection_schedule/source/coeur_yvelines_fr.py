from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.regions import Region
from waste_collection_schedule.service.CoeurYvelinesCalendar import (
    COMMUNES,
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Coeur d'Yvelines"
    DESCRIPTION = "Source script for coeur-yvelines.fr"
    URL = "https://www.coeur-yvelines.fr/"
    COUNTRY = "fr"
    TEST_CASES: ClassVar[dict] = {commune: {"commune": commune} for commune in COMMUNES}
    REGIONS = tuple(
        Region(
            title=commune,
            params={"commune": commune},
            url="https://www.coeur-yvelines.fr/",
        )
        for commune in COMMUNES
    )
    PARAMS = (municipality("commune"),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Déchets ménagers": wt.GENERAL_WASTE,
            "Déchets végétaux": wt.GARDEN_WASTE,
            "Emballages et papiers": wt.RECYCLABLES,
            "Encombrants": wt.BULKY_WASTE,
        },
    )
