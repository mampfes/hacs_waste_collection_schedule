from typing import ClassVar, final
from urllib.parse import quote

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://fosen.renovasjonsportal.no/api/address"


def _address_id(response, *, address: str, **_) -> str:
    """The search result whose title is the address, ignoring case."""
    data = response.json()
    if not data:
        raise SourceArgumentNotFound("address", address)
    wanted = address.lower().strip()
    for result in data["searchResults"]:
        if result["title"].lower().strip() == wanted:
            return result["id"]
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, [result["title"] for result in data["searchResults"]]
    )


@final
class Source(BaseSource):
    TITLE = "Fosen Renovasjon"
    DESCRIPTION = "Source for Fosen Renovasjon."
    URL = "https://fosenrenovasjon.no/"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Lysøysundveien 117": {"address": "Lysøysundveien 117"}
    }

    PARAMS = (street_address(),)

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                lambda address, **_: f"{_API_URL}/{quote(address.lower().strip())}",
                pick=_address_id,
            ),
        ),
        url=lambda address_id, **_: f"{_API_URL}/{address_id}/details",
        raise_for_status=True,
    )
    parse = parsers.JsonParser("disposals")
    transform = JsonTransformer(
        date_key=lambda disposal: disposal["date"][:10],
        type_key="fraction",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Restavfall til forbrenning": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Papir og plastemballasje": wt.PAPER,
        },
    )
