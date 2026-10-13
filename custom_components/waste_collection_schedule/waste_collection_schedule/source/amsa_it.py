import re
import zoneinfo
from typing import ClassVar, TypedDict, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import JsonTransformer

API = "https://www.amsa.it/api/service/area-services"


class _Item(TypedDict):
    """The fields the transformer reads from each calendar item."""

    date: int
    desc: str


def _suggestion(response, *_keys, address: str, **_) -> dict:
    """The first address the autocomplete offers for the typed address."""
    suggestions = response.json().get("data") or []
    if not suggestions:
        raise SourceArgumentNotFound("address", address)
    return suggestions[0]


def _geociv(response, suggestion: dict, *_keys, house_number: str, **_) -> str:
    """The civic id (geociv) the calendar is keyed by."""
    data = response.json().get("data") or {}
    geociv = data.get("idCivico") or data.get("place_id") or suggestion.get("id")
    if geociv is None:
        raise SourceArgumentNotFound("house_number", house_number)
    return str(geociv)


def _civic_number(house_number: str) -> int:
    """The numeric part of a house number ("40B" -> 40)."""
    digits = re.sub(r"\D", "", str(house_number))
    if not digits:
        raise SourceArgumentNotFound("house_number", house_number)
    return int(digits)


def _query(address: str, house_number: str, city: str | None = None, **_) -> str:
    query = f"{address} {house_number}"
    return f"{query}, {city}" if city else query


@final
class Source(BaseSource):
    TITLE = "AMSA"
    DESCRIPTION = "Source for AMSA (Milan, Italy) waste collection."
    URL = "https://www.amsa.it/it/milano"
    COUNTRY = "it"

    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "monte_rosa_91": {
            "address": "Via Monte Rosa",
            "house_number": "91",
            "city": "Milano",
        },
        "piazza_duomo_1": {
            "address": "Piazza del Duomo",
            "house_number": "1",
        },
        "viale_piave_40b": {
            "address": "Viale Piave",
            "house_number": "40B",
            "city": "Milano",
        },
    }

    PARAMS = (
        street("address"),
        house_number(),
        city(optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide the street name and house number of your address, "
            "as well as the city."
        ),
        "it": (
            "Devi fornire il nome della via e il numero civico del tuo indirizzo, "
            "oltre alla città."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.PLASTIC,
        wt.METAL,
        wt.GLASS,
        wt.OTHER,
    ]

    _TYPE_MAP: ClassVar[dict] = {
        "raccolta indifferenziato": wt.GENERAL_WASTE,
        "raccolta organico": wt.ORGANIC,
        "raccolta carta e cartone": wt.PAPER,
        "raccolta plastica e metallo": [wt.PLASTIC, wt.METAL],
        "raccolta plastica": wt.PLASTIC,
        "raccolta vetro": wt.GLASS,
        "raccolta vetro e metallo": [wt.GLASS, wt.METAL],
        "pulizia strade e marciapiedi": wt.OTHER,
    }

    # Three calls: address autocomplete, selection of the civic number (which
    # yields the civic id), then the calendar of that civic id.
    retrieve = retrievers.Request(
        f"{API}/calendar-items",
        method="POST",
        json=lambda suggestion, geociv, **_: {"geociv": geociv},
        before=(
            retrievers.Lookup(
                f"{API}/address-autocomplete",
                method="POST",
                json=lambda **params: {
                    "address": _query(**params),
                    "city": params.get("city") or "",
                    "source": "database",
                },
                pick=_suggestion,
            ),
            retrievers.Lookup(
                f"{API}/address-search",
                method="POST",
                json=lambda suggestion, house_number, city=None, **_: {
                    "id": suggestion.get("id"),
                    "street": suggestion.get("details", {}).get("via")
                    or suggestion.get("value"),
                    "city": city or "Milano",
                    "civic": _civic_number(house_number),
                },
                pick=_geociv,
            ),
        ),
    )

    parse = parsers.JsonParser("data", shape=list[_Item])

    transform = JsonTransformer(
        date_key="date",
        type_key="desc",
        parse_date=date_parsers.from_epoch(
            unit="ms", tz=zoneinfo.ZoneInfo("Europe/Rome")
        ),
        type_value_map=_TYPE_MAP,
    )
