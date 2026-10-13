from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.PowerBiWasteCalendar import (
    CalendarParser,
    calendar_retriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Ekonovus"
    DESCRIPTION = 'Source for UAB "Ekonovus" waste collection schedule.'
    URL = "https://www.ekonovus.lt"
    TEST_CASES: ClassVar[dict] = {
        "Margirio g. 16, Uzliedziai": {"address": "Margirio g. 16"}
    }
    COUNTRY = "lt"
    PARAMS = (street_address(),)

    retrieve = calendar_retriever
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Pakuotė": wt.RECYCLABLES,
            "Stiklas": wt.GLASS,
            "Komunalinės atliekos": wt.GENERAL_WASTE,
            "Komunalinės": wt.GENERAL_WASTE,
            "Žaliosios atliekos": wt.GARDEN_WASTE,
        },
    )
