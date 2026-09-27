from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Salford City Council"
    DESCRIPTION = "Source for bin collection services for Salford City Council, UK."
    URL = "https://www.salford.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "domestic": {"uprn": "100011404886"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.salford.gov.uk/bins-and-recycling/bin-collection-days/your-bin-collections/",
        params=lambda uprn, **_: {"UPRN": uprn},
    )
    # One column per bin: its name, then a list of dates.
    parse = parsers.HtmlLabelledDates(
        "div.col-12.col-lg-6:has(ul)",
        label="strong",
        date="ul",
        date_pattern=r"\w+ \d{2} \w+ \d{4}",
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        all_dates=True,
    )
    transform = RowTransformer(
        clean=lambda label: label.rstrip(":").strip(),
        type_value_map={
            "Domestic waste": wt.GENERAL_WASTE,
            "Blue recycling (paper and card)": wt.PAPER,
            "Pink recycling (glass, cans and plastic bottles)": wt.RECYCLABLES,
            "Brown recycling (bottles and cans)": wt.RECYCLABLES,
            "Food and garden waste": wt.ORGANIC,
        },
    )
