from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import HtmlTransformer

_SEARCH_URL = "https://api.hra.no/search/address"
_CALENDAR_URL = "https://hra.no/tommekalender/"

# Norwegian month abbreviations as the page prints them ("12. okt").
_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "okt": 10,
    "nov": 11,
    "des": 12,
}

# The round as the page's own legend names it. Norwegian is not a supported UI
# language, so every label is mapped here.
_TYPE_MAP = {
    "Restavfall": wt.GENERAL_WASTE,
    "Matavfall": wt.FOOD_WASTE,
    "Papir, papp og kartong": wt.PAPER,
    "Plastemballasje": wt.PLASTIC,
    "Glass- og metallemballasje": wt.GLASS,
}


def _normalize(value: str) -> str:
    return "".join(value.casefold().replace(",", "").split())


def _property(response, address, **_) -> tuple[str, str]:
    """The ``(name, agreement guid)`` of the one property the address names."""
    matches = response.json()
    norm = _normalize(address)
    exact = [m for m in matches if _normalize(m["name"]) == norm]
    if not exact:
        # Allow omitting postal code/place when the street address is unique.
        exact = [m for m in matches if _normalize(m["propertyName"]) == norm]
    if len(exact) == 1:
        return exact[0]["name"], exact[0]["agreementGuid"]
    candidates = exact or matches
    if not candidates:
        raise SourceArgumentNotFound("address", address)
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, sorted({m["name"] for m in candidates})
    )


def _date(row) -> str:
    """The row's year-less date as "12.10"."""
    text = row.find_parent("div", class_="garbage-retrieval-row").select_one(
        "span.date"
    )
    day, _, month = text.get_text(strip=True).partition(".")
    return f"{int(day)}.{_MONTHS[month.strip()[:3].lower()]}"


def _label(column) -> str:
    return column.find_all("div", recursive=False)[-1].get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "HRA (Hadeland og Ringerike Avfallsselskap)"
    DESCRIPTION = (
        "Source for HRA waste collection in Hadeland (Gran, Jevnaker, Lunner), Norway."
    )
    URL = "https://hra.no"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Myllavegen 1, 2742 GRUA": {"address": "Myllavegen 1, 2742 GRUA"},
        "Myllavegen 10": {"address": "Myllavegen 10"},
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.PLASTIC,
        wt.GLASS,
    ]

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search for your address at hra.no/tommekalender and use the address "
            "as shown in the result list, e.g. 'Myllavegen 1, 2742 GRUA'."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                _SEARCH_URL,
                params=lambda address, **_: {"query": address},
                raise_for_status=True,
                pick=_property,
            ),
        ),
        url=_CALENDAR_URL,
        params=lambda prop, **_: {"query": prop[0], "agreement": prop[1]},
        raise_for_status=True,
    )

    # One element per round of a collection day (the day's date is in the
    # row's first column, which has no nested label and is skipped).
    parse = HtmlParser("div.garbage-retrieval-row div.types > div:has(> div)")
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_label,
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.nearest_year("%d.%m"),
    )
