from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "London Borough of Southwark"
    DESCRIPTION = "Source for London Borough of Southwark waste collection."
    URL = "https://www.southwark.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "200003455089"},
        "Test_002": {"uprn": "200003379615"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        # The council's UPRNs are twelve digits, zero-padded.
        url=lambda uprn, **_: (
            f"https://services.southwark.gov.uk/bins/lookup/{str(uprn).zfill(12)}"
        ),
    )
    # "Next collection: Mon, 28 September 2026" in each service's block.
    parse = parsers.HtmlLabelledDates(
        "div.binProduct",
        label="p.h3:not(.hide-for-sr)",
        date="p:-soup-contains('Next collection:')",
        date_pattern=r"\d{1,2} \w+ \d{4}",
        parse_date=date_parsers.for_format("%d %B %Y"),
    )
    transform = RowTransformer(
        clean=lambda label: label.removesuffix(" Collection").strip(),
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Communal Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Communal Recycling": wt.RECYCLABLES,
            "Recycling Sack": wt.RECYCLABLES,
            "Food Waste": wt.FOOD_WASTE,
            "Communal Food": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
