from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.field_terms import DISTRICT
from waste_collection_schedule.service.CistoMestoCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Čisto mesto"
    DESCRIPTION = "Source for Čisto mesto Ptuj."
    URL = "https://cistomesto.si"
    COUNTRY = "si"
    TEST_CASES: ClassVar[dict] = {
        "Majšperk": {"region": "Majšperk"},
        "Cirkulane": {"region": "Cirkulane"},
        "Destrnik": {"region": "Destrnik"},
    }
    PARAMS = (text_field("region", term=DISTRICT),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Nevarni odpadki": wt.HAZARDOUS,
            "Kosovni odpadki": wt.BULKY_WASTE,
            "Pranje BIO posod": wt.OTHER,
            "Steklo": wt.GLASS,
            "Papir": wt.PAPER,
            "Mešani komunalni odpadki": wt.GENERAL_WASTE,
            "Biološki odpadki": wt.ORGANIC,
            "Mešana embalaža": wt.RECYCLABLES,
        },
    )
