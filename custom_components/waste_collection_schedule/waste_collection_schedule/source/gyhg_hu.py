from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "leftover": wt.GENERAL_WASTE,
    "recycle": wt.RECYCLABLES,
    "bio": wt.ORGANIC,
}


@final
class Source(BaseSource):
    TITLE = "Győri Hulladékgazdálkodási Nonprofit Kft."
    DESCRIPTION = "Source script using GYHG API at https://gyhg.bluespot.hu/api"
    URL = "https://www.gyhg.hu"
    COUNTRY = "hu"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_1": {"city": "Écs", "street": "Ady Endre utca", "house_number": "1/A"},
        "Test_2": {
            "city": "Mosonszentmiklós-Mosonújhely",
            "street": "Radnóti Miklós utca",
            "house_number": 25,
        },
        "Test_3": {
            "city": "Veszprémvarsány",
            "street": "Zrínyi utca",
            "house_number": 34,
        },
    }

    PARAMS = (city(), street(), house_number())

    HOWTO: ClassVar[dict] = {
        "en": "Select the desired address on the https://www.gyhg.hu/hulladeknaptar#/ website. The town, street name, and house number must be entered in this integration in the exact same format as they appear there.",
    }

    retrieve = HttpGetRetriever(
        url="https://gyhg.bluespot.hu/api/get_schedule",
        params=lambda city, street, house_number, **_: {
            "city_name": city,
            "street": street,
            "house_number": str(house_number),
        },
    )
    parse = parsers.KeyedDateListsParser("data", fields=_TYPE_MAP)
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map=_TYPE_MAP,
    )
