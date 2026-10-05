from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.BartecPublicDashboard import (
    BartecDashboardParser,
    BartecDashboardRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Scottish Borders Council"
    DESCRIPTION = "Source for Scottish Borders Council (Bartec Municipal)"
    URL = "https://scotborders-live-portal.bartecmunicipal.com/Embeddable/CollectionCalendar"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {"Test": {"uprn": "116073632", "postcode": "TD9 9HL"}}

    PARAMS = (postcode(), uprn())

    retrieve = BartecDashboardRetriever(
        "https://scotborders-live-portal.bartecmunicipal.com/Embeddable/CollectionCalendar"
    )
    parse = BartecDashboardParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
    )
