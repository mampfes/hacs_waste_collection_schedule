from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, house_number, street
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.service.TheHillsCalendar import (
    calendar_retriever,
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

    retrieve = calendar_retriever
    parse = parsers.JsonParser()
    preprocess = ExplodeList("CollectionDays", into="date")
    transform = JsonTransformer(
        date_key="date",
        type_key="Name",
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        type_value_map={"Rubbish": wt.GENERAL_WASTE, "Recycling": wt.RECYCLABLES},
    )
