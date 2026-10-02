from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import HtmlTransformer

BASE_URL = "https://www.alvsbynsenergi.se"

_FOOD = "Matavfall"
_BOTH = "Matavfall och Restavfall"


def _normalise(value: str) -> str:
    return " ".join(value.split()).casefold()


def _pick_street(response, *keys, address, **_) -> str:
    """The lookup answers ``{"suggestions": [{value, street_id, area_code, ...}]}``."""
    suggestions = response.json().get("suggestions", [])
    wanted = _normalise(address)
    matches = [
        s for s in suggestions if _normalise(s.get("value", "")).startswith(wanted)
    ]
    if (
        len(matches) != 1
        or not matches[0].get("street_id")
        or not matches[0].get("area_code")
    ):
        raise SourceArgumentNotFoundWithSuggestions(
            "address",
            address,
            sorted(
                s["value"].strip() for s in suggestions if s.get("value", "").strip()
            ),
        )
    return f"{matches[0]['street_id']}-{matches[0]['area_code']}"


def _date_text(item) -> str:
    """Each span reads "2026-10-15, Torsdag - matavfall"; the date leads."""
    return item.get_text(" ", strip=True)[:10]


def _type_text(item) -> str:
    """A date marked "matavfall" is the food bin only; an unmarked one is both."""
    return _FOOD if "matavfall" in item.get_text(" ", strip=True).casefold() else _BOTH


@final
class Source(BaseSource):
    TITLE = "Älvsbyns Energi"
    DESCRIPTION = "Waste collection schedule for Älvsbyns Energi, Sweden."
    URL = "https://www.alvsbynsenergi.se/"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.FOOD_WASTE, wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Storgatan 24": {"address": "Storgatan 24"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street address and house number as shown by the address "
            "search at https://www.alvsbynsenergi.se/ (for example, Storgatan 24)."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{BASE_URL}/assets/data/ajax.fetch_address.php",
                params=lambda address, **_: {"query": address},
                pick=_pick_street,
            ),
        ),
        url=lambda key, **_: f"{BASE_URL}/renhallning/sophamtning/{key}",
    )

    parse = parsers.HtmlParser(
        "#waste-empty-details > span", require=["#waste-empty-details"]
    )

    transform = HtmlTransformer(
        date_getter=_date_text,
        type_getter=_type_text,
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            _FOOD: wt.FOOD_WASTE,
            _BOTH: [wt.FOOD_WASTE, wt.GENERAL_WASTE],
        },
    )
