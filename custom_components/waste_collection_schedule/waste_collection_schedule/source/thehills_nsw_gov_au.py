from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, house_number, street
from waste_collection_schedule.service.TheHillsCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "The Hills Shire Council, Sydney"
    DESCRIPTION = "Source for Hills Shire Council, Sydney, Australia waste collection."
    URL = "https://www.thehills.nsw.gov.au/"
    TEST_CASES: ClassVar[dict] = {
        "Annangrove, Amanda Place 10": {
            "suburb": "ANNANGROVE",
            "street": "Amanda Place",
            "houseNo": 10,
        },
        "Annangrove, Amanda Place 10 (2)": {
            "suburb": "ANn ANgROvE",
            "street": "amanda PlaC e",
            "houseNo": " 10 ",
        },
    }
    COUNTRY = "au"
    PARAMS = (
        district("suburb"),
        street(),
        house_number("houseNo"),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={"Rubbish": wt.GENERAL_WASTE, "Recycling": wt.RECYCLABLES},
    )
