import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import RowTransformer

_API_URL = "https://my.oadby-wigston.gov.uk/my-property-finder"
_SEARCH_URL = "https://my.oadby-wigston.gov.uk/data/ac/addresses.json"

_year_less = date_parsers.nearest_year("%A %d %b")


def _normalise(address: str) -> str:
    return address.lower().replace(" ", "").replace(",", "")


def _address_id(response, address, **_):
    """The id of the suggestion whose label equals the configured address."""
    suggestions = response.json()
    if not suggestions:
        raise SourceArgumentNotFound("address", address)
    wanted = _normalise(address)
    for suggestion in suggestions:
        if _normalise(suggestion["label"]) == wanted:
            return suggestion["value"]
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, [suggestion["label"] for suggestion in suggestions]
    )


def _parse_date(text: str) -> datetime.date:
    """The page says "Today", "Tomorrow" or a year-less "Friday 9 Oct"."""
    lowered = text.strip().lower()
    if lowered == "today":
        return datetime.date.today()
    if lowered == "tomorrow":
        return datetime.date.today() + datetime.timedelta(days=1)
    return _year_less(text)


@final
class Source(BaseSource):
    TITLE = "Oadby and Wigston Council"
    DESCRIPTION = "Source for Oadby and Wigston Council."
    URL = "https://www.oadby-wigston.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "111, Main Street, Swithland": {
            "address": "56, Sussex Road, Wigston, Leicestershire"
        },
        "2, The Banks, Sileby": {
            "address": "89, Leicester Road, Leicester, Leicestershire"
        },
    }

    PARAMS = (street_address("address"),)

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the address exactly as the address search on "
            "[my.oadby-wigston.gov.uk](https://my.oadby-wigston.gov.uk/my-property-finder) "
            "suggests it, e.g. `56, Sussex Road, Wigston, Leicestershire`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _SEARCH_URL,
                params=lambda address, **_: {"term": address},
                pick=_address_id,
            ),
        ),
        url=_API_URL,
        params=lambda address_id, **_: {"address_id": address_id},
    )

    parse = parsers.HtmlLabelledDates(
        "div.refusecollectiondates li",
        label="a",
        date="strong",
    )

    transform = RowTransformer(
        parse_date=_parse_date,
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Food waste": wt.FOOD_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden waste": wt.GARDEN_WASTE,
        },
    )
