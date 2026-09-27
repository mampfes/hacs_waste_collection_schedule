from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Melton Borough Council"
    DESCRIPTION = "Source for waste collection services for Melton Borough Council, UK"
    URL = "https://www.melton.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100030544791"},
        "Test_002": {"uprn": 100030549260},
        "Test_003": {"uprn": "100030537000"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://my.melton.gov.uk/set-location",
        params=lambda uprn, **_: {
            "id": uprn,
            "redirect": "collections",
            "rememberloc": "",
        },
    )
    # "07/10/2026, and then 21/10/2026" under each round's heading.
    parse = parsers.HtmlLabelledDates(
        "li.box-item:has(h2)",
        label="h2",
        date="strong",
        date_pattern=r"\d{2}/\d{2}/\d{4}",
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        all_dates=True,
    )
    transform = RowTransformer(
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
