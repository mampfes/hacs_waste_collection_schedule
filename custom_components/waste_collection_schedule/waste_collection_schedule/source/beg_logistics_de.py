from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, house_number, street
from waste_collection_schedule.service.BegLogistics import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Bremerhavener Entsorgungsgesellschaft mbH"
    DESCRIPTION = "Source for Bremerhavener Entsorgungsgesellschaft mbH."
    URL = "https://beg-bhv.de"
    COUNTRY = "de"
    TEST_CASES: ClassVar[dict] = {
        "Hafenstraße 22": {"street": "Hafenstraße, Bremerhaven", "hnr": 2},
        "Hadeler Heide, Cuxhaven": {
            "street": "Hadeler Heide, Cuxhaven",
            "hnr": "2",
            "two_weeks": True,
        },
    }
    PARAMS = (
        street(),
        house_number("hnr"),
        boolean("two_weeks", "Fortnightly collection", default=False),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Graue tonne": wt.GENERAL_WASTE,
            "Blaue tonne": wt.PAPER,
            "Gelber sack": wt.RECYCLABLES,
            "Gelbe tonne": wt.RECYCLABLES,
            "Tannenbaum": wt.GARDEN_WASTE,
            "Gelbe tonneTannenbaum": [wt.RECYCLABLES, wt.GARDEN_WASTE],
        },
    )
