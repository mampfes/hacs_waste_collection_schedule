from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.WebAspxCollections import (
    TYPE_VALUE_MAP,
    CalendarParser,
    calendar_retriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Mid Ulster District Council"
    DESCRIPTION = "Source for Mid Ulster District Council, UK."
    URL = "https://www.midulstercouncil.org"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "185653615": {"uprn": 185653615},
        "185653617": {"uprn": "185653617"},
        "185653613": {"uprn": "185653613"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering your address details."
        ),
    }

    retrieve = calendar_retriever("collections-midulster.azurewebsites.net", "MUL")
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map=TYPE_VALUE_MAP,
    )
