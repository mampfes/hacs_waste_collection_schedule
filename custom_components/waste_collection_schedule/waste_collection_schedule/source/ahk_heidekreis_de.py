from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, postcode, street
from waste_collection_schedule.service.HeidekreisCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "AHK Heidekreis"
    DESCRIPTION = "Source for AHK Heidekreis, Germany (ahk-heidekreis.de)"
    URL = "https://www.ahk-heidekreis.de"
    TEST_CASES: ClassVar[dict] = {
        "Munster, Wagnerstr. 10-18": {
            "city": "Munster",
            "postcode": "29633",
            "street": "Wagnerstr.",
            "house_number": "10-18",
        },
        "Fallingbostel, Konrad-Zuse-Str. 4": {
            "city": "Fallingbostel/Bad Fallingbostel",
            "postcode": 29683,
            "street": "Konrad-Zuse-Str.",
            "house_number": 4,
        },
    }
    COUNTRY = "de"
    PARAMS = (
        city(),
        postcode(),
        street(),
        house_number(),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Restabfall": wt.GENERAL_WASTE,
            "AHS RM 1100 L": wt.GENERAL_WASTE,
            "Gelbe Tonne 1100 L": wt.RECYCLABLES,
            "Gelbe Tonne": wt.RECYCLABLES,
            "Bioenergie": wt.ORGANIC,
            "Bio- und Garten": wt.ORGANIC,
            "Garten": wt.GARDEN_WASTE,
            "Papier": wt.PAPER,
        },
    )
