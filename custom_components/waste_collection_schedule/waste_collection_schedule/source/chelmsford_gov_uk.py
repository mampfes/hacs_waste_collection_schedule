from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

_MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|"
    "November|December"
)

_TYPE_MAP = {
    "food waste": wt.FOOD_WASTE,
    "black bin": wt.GENERAL_WASTE,
    "brown bin": wt.GARDEN_WASTE,
    "green box": wt.GLASS,
    "paper sack": wt.PAPER,
    "card sack": wt.PAPER,
    "plastic and cartons bag": wt.RECYCLABLES,
}


@final
class Source(BaseSource):
    TITLE = "Chelmsford City Council"
    DESCRIPTION = "Source for Chelmsford City Council, UK"
    URL = "https://www.chelmsford.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.GLASS,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"collection_round": "Tuesday A"},
        "Test_002": {"collection_round": "Thursday B"},
    }

    PARAMS = (text_field("collection_round", "Collection round"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your collection round (e.g. Tuesday A) by visiting "
            "https://www.chelmsford.gov.uk/bins-and-recycling/check-your-collection-day "
            "and entering in your address details."
        ),
    }

    retrieve = HttpGetRetriever(
        url=lambda collection_round, **_: (
            "https://www.chelmsford.gov.uk/bins-and-recycling/check-your-collection-day/"
            f"{collection_round.lower().replace(' ', '-')}-collection-calendar/"
        ),
    )
    parse = parsers.HtmlTextParser(separator="\n", collapse_whitespace=False)
    # The page lists "<Month> <year>" headings, each followed by
    # "Tuesday 6 October: food waste, black bin, ..." lines.
    preprocess = preprocessors.TextDatedBlocks(
        block_pattern=r"(?m)^\s*\w+day\s+(?P<day>\d{1,2})\s+(?P<month>[A-Za-z]+):\s*(?P<labels>[^\n]+)",
        label_separator=r",",
        year_pattern=rf"(?m)^\s*(?:{_MONTHS})\s+(\d{{4}})\s*$",
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
