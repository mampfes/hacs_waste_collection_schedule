from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.service.KomLubCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "KOM-LUB (Luboń, PL)"
    DESCRIPTION = (
        "Scrapes waste collection schedule by district (1..7) from kom-lub.com.pl."
    )
    URL = "https://kom-lub.com.pl/aktualny-harmonogram-wywozow/"
    TEST_CASES: ClassVar[dict] = {
        "TestDistrict1": {"district": 1},
        "TestDistrict2": {"district": 2},
        "TestDistrict3": {"district": 3},
        "TestDistrict4": {"district": 4},
        "TestDistrict5": {"district": 5},
        "TestDistrict6": {"district": 6},
        "TestDistrict7": {"district": 7},
    }
    HOWTO: ClassVar[dict] = {
        "en": "Enter your district number (1–7). Your district (R I through R VII) is printed on your bin collection notice or can be found on the KOM-LUB website (https://kom-lub.com.pl)."
    }
    COUNTRY = "pl"
    PARAMS = (district(),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Mixed": wt.GENERAL_WASTE,
            "Glass": wt.GLASS,
            "Plastics": wt.PLASTIC,
            "Paper": wt.PAPER,
            "Bulky": wt.BULKY_WASTE,
            "Bio": wt.ORGANIC,
        },
    )
