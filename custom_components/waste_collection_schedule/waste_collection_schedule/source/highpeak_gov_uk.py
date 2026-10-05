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
    TITLE = "High Peak Borough Council"
    DESCRIPTION = "Source for High Peak Borough Council."
    URL = "https://www.highpeak.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "SK23 6BQ 10010724045": {"postcode": "SK23 6BQ", "uprn": 10010724045},
        "S33 7ZA, 10010747174": {"postcode": "S33 7ZA", "uprn": "10010747174"},
        " SK13 2AD, 10010734345": {"postcode": "SK13 2AD", "uprn": "10010734345"},
    }

    PARAMS = (postcode(), uprn())

    retrieve = BartecDashboardRetriever("https://bins.highpeak.gov.uk/PublicDashboard")
    parse = BartecDashboardParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
    )
