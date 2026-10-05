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
    TITLE = "Staffordshire Moorlands District Council"
    DESCRIPTION = "Source for waste collection services for Staffordshire Moorlands District Council, UK."
    URL = "https://www.staffsmoorlands.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Managers Accommodation Roaring Meg (ST8 7EA)": {
            "postcode": "ST8 7EA",
            "uprn": "10010602737",
        },
        "34 Pennine Way, Biddulph (ST8 7EA)": {
            "postcode": "ST8 7EA",
            "uprn": "100031858191",
        },
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": "Your UPRN can be found by searching your postcode at "
        "https://www.staffsmoorlands.gov.uk/findyourbinday (which redirects "
        "to the council's Public Dashboard) and selecting your address. The "
        "value shown in the address dropdown is your UPRN. Alternatively, "
        "find your UPRN at https://www.findmyaddress.co.uk/"
    }

    retrieve = BartecDashboardRetriever(
        "https://bins.staffsmoorlands.gov.uk/PublicDashboard"
    )
    parse = BartecDashboardParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
    )
