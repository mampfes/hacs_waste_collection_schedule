from typing import ClassVar, final

from waste_collection_schedule import date_parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.WebAspxCollections import (
    TYPE_VALUE_MAP,
    CalendarParser,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Ards and North Down Borough Council"
    DESCRIPTION = "Source for Ards and North Down Borough Council."
    URL = "https://ardsandnorthdown.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "185833845": {"uprn": 185833845},
        "187340776": {"uprn": "185928695"},
        "185180798": {"uprn": 185180798},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering your address details."
        ),
    }

    retrieve = retrievers.Request(
        lambda uprn, **_: (
            "https://ardsandnorthdownbincalendar.azurewebsites.net"
            f"/api/calendarhtml/{str(uprn).strip()}"
        )
    )
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map=TYPE_VALUE_MAP,
    )
