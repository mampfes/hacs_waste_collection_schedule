from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import JsonTransformer

_TYPE_MAP = {
    "FOODCAD": wt.FOOD_WASTE,
    "BLUEBOX": wt.PAPER,
    "GREENBOX": wt.GLASS,
    "BLUEBAG": wt.RECYCLABLES,
    "REDBAG": wt.PLASTIC,
    "GREYBAG": wt.GENERAL_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Pembrokeshire County Council"
    DESCRIPTION = "Source for pembrokeshire.gov.uk"
    URL = "https://www.pembrokeshire.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.PLASTIC,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Dew Street": {"uprn": "100100283349"},
        "Heol Cleddau": {"uprn": "100100281816"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "To get your UPRN go to [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) "
            "and search for your address."
        ),
    }

    retrieve = retrievers.Request(
        "https://www.pembrokeshire.gov.uk/template/waste/api.asp",
        method="POST",
        data="",
        params=lambda uprn, **_: {
            "action": "dates",
            "public": "true",
            "uprn": str(uprn),
            "language": "eng",
        },
    )

    parse = parsers.ArgumentGuard(
        parsers.JsonParser("bins"),
        argument="uprn",
        contains='"error":"false"',
        hint="check your UPRN at https://www.findmyaddress.co.uk/",
    )

    transform = JsonTransformer(
        date_key="nextdate",
        type_key="type",
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
