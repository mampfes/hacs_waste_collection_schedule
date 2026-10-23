from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.service.EthErdCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "ÉTH (Érd, Diósd, Ráckeresztúr, Sóskút, Tárnok)"
    DESCRIPTION = "Source script for www.eth-erd.hu"
    URL = "https://www.eth-erd.hu"
    COUNTRY = "hu"
    TEST_CASES: ClassVar[dict] = {
        "Test_Erd_Hordo": {"city": "Érd", "street": "Hordó utca"},
        "Test_Diosd_Diofasor": {"city": "Diósd", "street": "Diófasor utca"},
        "Test_Soskut_Ady": {"city": "Sóskút", "street": "Ady Endre utca"},
        "Test_Tarnok_Amur": {"city": "Tárnok", "street": "Amur utca"},
        "Test_Rackeresztur_Ady": {"city": "Ráckeresztúr", "street": "Ady Endre utca"},
    }
    PARAMS = (
        city(),
        street(),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Communal": wt.GENERAL_WASTE,
            "Selective": wt.RECYCLABLES,
            "Green": wt.GARDEN_WASTE,
            "Glass": wt.GLASS,
        },
    )
