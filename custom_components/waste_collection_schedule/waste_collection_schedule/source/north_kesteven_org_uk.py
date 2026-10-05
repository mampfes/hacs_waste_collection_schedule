from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "North Kesteven District Council"
    DESCRIPTION = (
        "Source for n-kesteven.org.uk services for North Kesteven District Council, UK."
    )
    URL = "https://n-kesteven.org.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100030860713"},
        "Test_002": {"uprn": "10006514327"},
        "Test_003": {"uprn": "100030857039"},
        "Test_004": {"uprn": 100030864449},
        "Test_005": {"uprn": 10006507163},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.n-kesteven.org.uk/bins/display",
        params=lambda uprn, **_: {"uprn": uprn},
    )
    # "<span>Black</span> (Residual waste) bin on <strong>Tuesday, 29
    # September 2026</strong>", one list item per bin.
    parse = parsers.HtmlLabelledDates(
        ".bin-dates li:has(strong)",
        label="span.font-weight-bold",
        date="strong",
        parse_date=date_parsers.for_format("%A, %d %B %Y"),
    )
    transform = RowTransformer(
        type_value_map={
            "Black": wt.GENERAL_WASTE,
            "Silver": wt.RECYCLABLES,
            "Purple": wt.RECYCLABLES,
            "Orange lidded caddy": wt.FOOD_WASTE,
            "Brown": wt.GARDEN_WASTE,
        },
    )
