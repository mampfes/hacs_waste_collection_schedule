from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "Waste collection dates": wt.GENERAL_WASTE,
    "Recycling collection dates": wt.RECYCLABLES,
    "Glass recycling collection dates": wt.GLASS,
    "Food waste collection dates": wt.FOOD_WASTE,
    "Garden waste collection dates": wt.GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Basingstoke and Deane Borough Council"
    DESCRIPTION = "Source for basingstoke.gov.uk services for Basingstoke and Deane Borough Council, UK."
    URL = "https://basingstoke.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100060234732"},
        "Test_002": {"uprn": "100060218986"},
        "Test_003": {"uprn": 100060235836},
        "Test_004": {"uprn": 100060224194},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)."
        ),
    }

    retrieve = retrievers.Request(
        "https://www.basingstoke.gov.uk/bincollections",
        cookies=lambda uprn, **_: {
            "cookie_control_popup": "N",
            "WhenAreMyBinsCollected": str(uprn),
        },
    )

    parse = parsers.HtmlLabelledDates(
        "div.service",
        label="h2",
        date="ul",
        date_pattern=r"(\d{1,2} [A-Za-z]+ \d{4})",
        all_dates=True,
    )

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map=_TYPE_MAP,
    )
