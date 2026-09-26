from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.NorthYorkshireBinCalendar import (
    TYPE_VALUE_MAP,
    BinCalendarParser,
    bin_calendar_retriever,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "North Yorkshire Council - Scarborough"
    DESCRIPTION = "Source for North Yorkshire Council - Scarborough."
    URL = "https://northyorks.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "100052176620": {"uprn": 100050497178},
        "10013454353": {"uprn": "100052161572"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Look your property up on the [North Yorkshire Council bin calendar]"
            "(https://www.northyorks.gov.uk/bin-calendar/lookup). Your UPRN is the "
            "number at the end of the results page's URL, e.g. "
            "`https://www.northyorks.gov.uk/bin-calendar/Scarborough/results/100050497178`."
        ),
    }

    retrieve = bin_calendar_retriever("Scarborough")
    parse = BinCalendarParser()
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map=TYPE_VALUE_MAP,
    )
