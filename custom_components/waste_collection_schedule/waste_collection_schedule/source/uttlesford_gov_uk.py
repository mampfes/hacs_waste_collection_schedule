import re
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer


def _date_text(row: Tag) -> str:
    # "Tuesday 6th October": the year is missing and the day has an ordinal suffix.
    return re.sub(r"(\d)(st|nd|rd|th)", r"\1", row.select("td")[1].get_text().strip())


def _bin(row: Tag) -> str:
    # The alt text of the images is wrong on the website, so go by the image itself.
    image = row.select_one("td img")
    return "green" if image is not None and "green" in str(image["src"]) else "black"


@final
class Source(BaseSource):
    TITLE = "Uttlesford District Council"
    DESCRIPTION = "Source for uttlesford.gov.uk, Uttlesford District Council, UK"
    URL = "https://www.uttlesford.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Brook Cottage, CM6 1LW": {"house": "29142-Tuesday"},
        "Springfields, CM6 1BP": {"house": "26455-Thursday"},
    }

    PARAMS = (text_field("house", label="House"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to https://bins.uttlesford.gov.uk/ and look up your address. "
            "The house value is the `house` parameter of the results page "
            "address (`collections.php?house=29142-Tuesday`)."
        ),
    }

    retrieve = HttpGetRetriever(
        url="https://bins.uttlesford.gov.uk/collections.php",
        params=lambda house, **_: {"house": house},
    )
    parse = parsers.HtmlParser("tr:has(td)")
    transform = HtmlTransformer(
        date_getter=_date_text,
        type_getter=_bin,
        parse_date=date_parsers.nearest_year("%A %d %B"),
        # Every collection also includes the brown food waste bin.
        type_value_map={
            "black": [wt.GENERAL_WASTE, wt.FOOD_WASTE],
            "green": [wt.RECYCLABLES, wt.FOOD_WASTE],
        },
    )
