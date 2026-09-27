from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Darlington Borough Council"
    DESCRIPTION = "Source for Darlington Borough Council."
    URL = "https://darlington.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "10013321444": {"uprn": 10013321444},
        "010013315817": {"uprn": 10013315817},
        "100110560916": {"uprn": 100110560916},
        "200002724471": {"uprn": "200002724471"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.darlington.gov.uk/bins-waste-and-recycling/collection-day-lookup/",
        params=lambda uprn, **_: {"uprn": uprn},
    )
    # One card per date, listing every round collected on it.
    parse = parsers.HtmlLabelledDates(
        "div.refuse-results",
        label=".collection-result-text",
        date=".collectionDate p",
        date_pattern=r"\w+ \d{1,2} \w+ \d{4}",
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        all_labels=True,
    )
    transform = RowTransformer(
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food waste": wt.FOOD_WASTE,
            "Garden waste": wt.GARDEN_WASTE,
        },
    )
