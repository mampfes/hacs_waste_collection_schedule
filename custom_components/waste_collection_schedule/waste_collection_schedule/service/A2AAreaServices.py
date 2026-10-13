"""The A2A area-services API: autocomplete, civic lookup, then dated collections."""

import re

from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import Lookup, Request


def _suggestion(response, *_keys, address: str, **_) -> dict:
    suggestions = response.json().get("data") or []
    if not suggestions:
        raise SourceArgumentNotFound("address", address)
    return suggestions[0]


def _geociv(response, suggestion: dict, *_keys, house_number: str, **_) -> str:
    data = response.json().get("data") or {}
    geociv = data.get("idCivico") or data.get("place_id") or suggestion.get("id")
    if geociv is None:
        raise SourceArgumentNotFound("house_number", house_number)
    return str(geociv)


def _civic_number(house_number: str) -> int:
    digits = re.sub(r"\D", "", str(house_number))
    if not digits:
        raise SourceArgumentNotFound("house_number", house_number)
    return int(digits)


def calendar_retriever(site: str) -> Request:
    """Configure the shared three-request calendar flow for an A2A deployment."""
    api = f"{site}/api/service/area-services"
    headers = {"Origin": site, "Referer": f"{site}/it?popup=services&serviceType=sdz"}
    return Request(
        f"{api}/calendar-items",
        method="POST",
        headers=headers,
        json=lambda suggestion, geociv, **_: {"geociv": geociv},
        before=(
            Lookup(
                f"{api}/address-autocomplete",
                method="POST",
                headers=headers,
                json=lambda address, house_number, city, **_: {
                    "address": f"{address} {house_number}, {city}",
                    "city": city,
                    "source": "database",
                },
                pick=_suggestion,
            ),
            Lookup(
                f"{api}/address-search",
                method="POST",
                headers=headers,
                json=lambda suggestion, house_number, city, **_: {
                    "id": suggestion.get("id"),
                    "street": suggestion.get("details", {}).get("via")
                    or suggestion.get("value"),
                    "city": city,
                    "civic": _civic_number(house_number),
                },
                pick=_geociv,
            ),
        ),
    )
