from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Flintshire"
    DESCRIPTION = "Source for Flintshire, United Kingdom."
    URL = "https://flintshire.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "100100211557": {"uprn": 100100211557},
        "200001744973": {"uprn": "200001744973"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpPostRetriever(
        url=lambda uprn, **_: (
            f"https://digital.flintshire.gov.uk/FCC_BinDay/Home/Details2/{uprn}"
        ),
    )
    # One row per date: date, weekday, then the rounds separated by "/".
    parse = parsers.HtmlLabelledDates(
        "div.col-md-12",
        label="div:nth-of-type(3)",
        date="div:nth-of-type(1)",
        label_separator="/",
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
    transform = RowTransformer(
        type_value_map={
            "Black Bin": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food": wt.FOOD_WASTE,
            "Garden": wt.GARDEN_WASTE,
            "Brown Bin": wt.GARDEN_WASTE,
        },
    )
