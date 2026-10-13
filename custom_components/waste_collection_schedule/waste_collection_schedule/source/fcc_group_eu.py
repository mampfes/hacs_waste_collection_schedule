from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, dropdown, text_field
from waste_collection_schedule.field_terms import DISTRICT
from waste_collection_schedule.service.KabernetCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "fcc Environment"
    DESCRIPTION = "Source for fcc Environment."
    URL = "https://www.fcc-group.eu/"
    TEST_CASES: ClassVar[dict] = {
        "Cífer J. Kubányiho": {"city": "Cífer", "location": "J. Kubányiho"},
        "Borinka Weekly": {"city": "Borinka", "frequency": "weekly"},
        "Cerová Monthly": {"city": "Cerová", "frequency": "monthly"},
    }
    COUNTRY = "sk"
    PARAMS = (
        city(),
        text_field("location", term=DISTRICT, optional=True),
        dropdown(
            "frequency",
            ["weekly", "biweekly", "monthly"],
            "Collection frequency",
            optional=True,
        ),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        # The rest of each label identifies the container (bags or bins).
        clean=lambda label: label.split()[0],
        type_value_map={
            "Komunálny": wt.GENERAL_WASTE,
            "Plasty": wt.PLASTIC,
            "Papier": wt.PAPER,
            "Separovaný": wt.RECYCLABLES,
        },
    )
