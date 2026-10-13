from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.lookups import normalize_loose
from waste_collection_schedule.transformers import RowTransformer

_SEARCH_URL = "https://my.charnwood.gov.uk/data/ac/addresses.json"
_PROPERTY_URL = "https://my.charnwood.gov.uk/my-property-finder"

_TYPE_MAP = {
    "Refuse": wt.GENERAL_WASTE,
    "Garden Waste": wt.GARDEN_WASTE,
    "Recycling": wt.RECYCLABLES,
}


def _pick_address_id(response, *_, address, **__) -> str:
    """The address search answers ``[{"label": ..., "value": id}, ...]``."""
    data = response.json()
    if not data:
        raise SourceArgumentNotFound("address", address)

    wanted = normalize_loose(address)
    for entry in data:
        if normalize_loose(entry["label"]) == wanted:
            return entry["value"]
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, [entry["label"] for entry in data]
    )


@final
class Source(BaseSource):
    TITLE = "Charnwood"
    DESCRIPTION = "Source for Charnwood Borough Council."
    URL = "https://www.charnwood.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "111, Main Street, Swithland": {"address": "111, Main Street, Swithland"},
        "2, Banks Close, Sileby": {"address": "2, Banks Close, Sileby"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address exactly as the council's address search lists it, "
            "for example `111, Main Street, Swithland`."
        ),
    }

    # The property page redirects through /location, which sets the cookie the
    # page needs, so the session has to follow the redirects.
    retrieve = retrievers.Request(
        _PROPERTY_URL,
        params=lambda address_id, **_: {"address_id": address_id},
        before=(
            retrievers.Lookup(
                _SEARCH_URL,
                params=lambda address, **_: {"term": address},
                pick=_pick_address_id,
            ),
        ),
    )

    parse = parsers.HtmlLabelledDates(
        "div.refusecollectiondates ul.refuse li",
        label="a",
        date="strong.date",
        parse_date=date_parsers.relative_words(
            date_parsers.without_ordinals(date_parsers.nearest_year("%a %d %b"))
        ),
    )

    transform = RowTransformer(type_value_map=_TYPE_MAP)
