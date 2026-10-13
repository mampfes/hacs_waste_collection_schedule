from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import ICSTransformer

_SEARCH_URL = "https://www.pireva.se/api/search/collection-address"
_SCHEDULE_URL = "https://www.pireva.se/tomningsschema/{slug}/"

_TYPE_MAP = {
    "restavfall": wt.GENERAL_WASTE,
    "matavfall": wt.FOOD_WASTE,
}


def _pick_slug(response, *, street_address: str, **_) -> str:
    matches = response.json().get("matches", [])
    for item in matches:
        if item.get("address") == street_address:
            return item["address_slug"]
    raise SourceArgumentNotFoundWithSuggestions(
        "street_address", street_address, [m["address"] for m in matches]
    )


@final
class Source(BaseSource):
    TITLE = "Pireva"
    DESCRIPTION = "Source for Pireva that serves Piteå kommun, Sweden."
    URL = "https://www.pireva.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Räddningstjänsten Mf": {
            "street_address": "Kolugnsvägen 1 Räddningstjänsten Mf"
        },
        "Oskarsvägen 20": {"street_address": "Oskarsvägen 20"},
    }

    PARAMS = (street_address(field="street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address exactly as it is written in the address search "
            "on https://www.pireva.se/tomningsschema/ (street, number and, for "
            "some properties, a name, e.g. 'Kolugnsvägen 1 Räddningstjänsten Mf')."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _SEARCH_URL,
                params=lambda street_address, **_: {"q": street_address},
                pick=_pick_slug,
            ),
        ),
        url=lambda slug, **_: _SCHEDULE_URL.format(slug=slug),
    )
    # One table per month, headed "Oktober" (this year) or "Januari 2027"; each
    # row is the waste type and "Torsdag 15 oktober".
    parse = parsers.HtmlMonthHeadedRows(
        all_tables=True,
        day_column=1,
        label_column=0,
        day_pattern=r"(\d{1,2})",
        current_year=True,
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
