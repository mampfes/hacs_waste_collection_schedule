from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import Deduplicate
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Wakefield Council"
    DESCRIPTION = "Source for Wakefield.gov.uk services for Wakefield Council"
    URL = "https://wakefield.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "uprn1": {"uprn": "63024087"},
        "uprn2": {"uprn": 63105305},
        "uprn3": {"uprn": "63012193"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.wakefield.gov.uk/where-i-live/",
        # The page needs the "a" parameter present; its value does not matter.
        params=lambda uprn, **_: {"uprn": uprn, "a": "Your Address"},
    )
    # One box per bin: its name, then its last, next and future dates
    # ("Next collection - Thursday, 1 October 2026").
    parse = parsers.HtmlLabelledDates(
        ".tablet\\:l-col-fb-4.u-mt-10",
        label="strong",
        date=":scope",
        date_pattern=r"\d{1,2} [A-Z][a-z]+ \d{4}",
        parse_date=date_parsers.for_format("%d %B %Y"),
        all_dates=True,
    )
    preprocess = Deduplicate()
    transform = RowTransformer(
        type_value_map={
            "Household waste": wt.GENERAL_WASTE,
            "Mixed recycling": wt.RECYCLABLES,
            "Garden waste recycling": wt.GARDEN_WASTE,
        },
    )
