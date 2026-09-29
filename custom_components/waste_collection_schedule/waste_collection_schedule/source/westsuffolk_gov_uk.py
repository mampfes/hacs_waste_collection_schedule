import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import RowTransformer

# The council: green-lidded bin for paper and card, blue bin for mixed
# recycling, brown bin for the paid garden waste service.
_TYPE_MAP = {
    "Black Bins": wt.GENERAL_WASTE,
    "Blue Bins": wt.RECYCLABLES,
    "Brown Bins": wt.GARDEN_WASTE,
    "Food Bins": wt.FOOD_WASTE,
    "Green Bins": wt.PAPER,
}

# "Food Bins: Tuesday 29th September": the page states no year.
_ENTRY = re.compile(
    r"(?P<label>[A-Za-z]+ Bins):\s*[A-Za-z]+\s+(?P<day>\d{1,2})(?:st|nd|rd|th)?\s+(?P<month>[A-Za-z]+)"
)


def _entries(text: str, source=None) -> Iterable[tuple[str, str]]:
    """The ``(day month, label)`` rows of the page's "next bin collection days" list."""
    for match in _ENTRY.finditer(text):
        yield f"{match['day']} {match['month']}", match["label"]


@final
class Source(BaseSource):
    TITLE = "West Suffolk Council"
    DESCRIPTION = "Source for West Suffolk Council."
    URL = "https://westsuffolk.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Flat, The Flying Shuttle, Three Counties Way, Withersfield, CB9 7FB": {
            "uprn": 10090739388
        },
        "Haere Mai, The Street, Troston, IP31 1EW": {"uprn": "100091387226"},
    }

    PARAMS = (uprn(),)

    retrieve = retrievers.HttpGetRetriever(
        "https://maps.westsuffolk.gov.uk/MyWestSuffolk.aspx",
        params=lambda uprn, **_: {"UniqueId": uprn, "action": "SetAddress"},
    )

    parse = parsers.HtmlTextParser()

    preprocess = staticmethod(_entries)

    transform = RowTransformer(
        parse_date=date_parsers.nearest_year("%d %B"),
        type_value_map=_TYPE_MAP,
    )
