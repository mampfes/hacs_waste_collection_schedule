from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Maldon District Council"
    DESCRIPTION = "Source for www.maldon.gov.uk services for Maldon, UK"
    URL = "https://www.maldon.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "test 1": {"uprn": "200000917928"},
        "test 2": {"uprn": 100091258454},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://maldon.suez.co.uk/maldon/ServiceSummary",
        params=lambda uprn, **_: {"uprn": uprn},
    )
    # One panel per service, carrying its last and next collection.
    parse = parsers.HtmlLabelledDates(
        "div.panel-default",
        label="h2.panel-title",
        date=".panel-body",
        date_pattern=r"\d{2}/\d{2}/\d{4}",
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        all_dates=True,
    )
    transform = RowTransformer(
        type_value_map={
            "Refuse Collection": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
            "Food Waste Collection": wt.FOOD_WASTE,
            "Other Services": None,
        },
    )
