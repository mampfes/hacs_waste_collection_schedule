import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer

# One box per bin: "Your next Blue bin collection" and "30th September" (no
# year).

_parse = date_parsers.nearest_year("%d %B")


@final
class Source(BaseSource):
    TITLE = "Wyre Borough Council"
    DESCRIPTION = "Source script for wyre.gov.uk"
    URL = "https://www.wyre.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "10094000847"},
        "Test_002": {"uprn": "100010727065"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.wyre.gov.uk/bincollections",
        # The council's UPRNs are twelve digits, zero-padded.
        params=lambda uprn, **_: {"uprn": str(uprn).zfill(12)},
    )
    parse = parsers.HtmlLabelledDates(
        "div.boxed:has(.bin-collection-tasks__heading)",
        label=".bin-collection-tasks__heading",
        date=".bin-collection-tasks__date",
        parse_date=lambda text: _parse(re.sub(r"(\d)(st|nd|rd|th)", r"\1", text)),
    )
    transform = RowTransformer(
        clean=lambda label: (
            label.removeprefix("Your next").removesuffix("collection").strip()
        ),
        type_value_map={
            "Grey bin": wt.GENERAL_WASTE,
            "Red bin": wt.RECYCLABLES,
            "Blue bin": wt.PAPER,
            "Green bin": wt.GARDEN_WASTE,
            "Food caddy": wt.FOOD_WASTE,
        },
    )
