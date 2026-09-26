"""ReCollect (Routeware) platform: the JSON events API behind its widgets.

ReCollect also publishes each place's schedule as an ``.ics`` export, which the
generic ICS source reads (``doc/ics/yaml/recollect.yaml``). This module is the
JSON side of the same data, for when that export is unavailable: the events
endpoint takes the same ``place_id`` and ``service_id`` as the ICS link.

A place lives on exactly one of two hosts (North America or Europe); the other
answers 404. :func:`events_retriever` tries both in turn, and
:class:`ReCollectEventsParser` turns the reply into ``(date, label)`` rows,
keeping pickups and dropping holiday and notice flags.

For a municipality whose users know their address rather than their place id,
:func:`address_suggest_retriever` resolves the address through the area's own
address search first, then requests the same events.
"""

import datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from waste_collection_schedule import response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import FirstMatchRetriever, TwoStepRetriever

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

API_HOSTS = ("https://api.recollect.net", "https://api.eu.recollect.net")
EVENTS_PATH = "/api/places/{place_id}/services/{service_id}/events"
SUGGEST_PATH = "/api/areas/{area}/services/{service_id}/address-suggest"

# Labels ReCollect municipalities use that the shared vocabulary does not
# resolve verbatim. Municipalities name their own streams, so anything not
# listed here or in the vocabulary is preserved as sent.
TYPE_VALUE_MAP = {
    "Blue Box": wt.RECYCLABLES,
    "Green Cart": wt.ORGANIC,
    "Bulk Waste (3 items max)": wt.BULKY_WASTE,
    "Garbage (Six Bags Maximum, No Tags Required)": wt.GENERAL_WASTE,
    "Non-recyclable Waste": wt.GENERAL_WASTE,
    "Plastic, cans and cartons": wt.RECYCLABLES,
}


def _events_query(locale: str) -> dict[str, str]:
    """The events query: 30 days back to a year ahead, the span the widget shows."""
    today = datetime.date.today()
    return {
        "hide": "reminder_only",
        "after": (today - datetime.timedelta(days=30)).isoformat(),
        "before": (today + datetime.timedelta(days=365)).isoformat(),
        "locale": locale,
    }


def events_retriever(
    place_id: str = "place_id", service_id: str = "service_id", locale: str = "locale"
) -> FirstMatchRetriever:
    """The events request, tried on each ReCollect host until one serves it.

    The arguments name the source's params holding each value.
    """
    return FirstMatchRetriever(
        candidates=API_HOSTS,
        url=lambda candidate, **params: (
            candidate
            + EVENTS_PATH.format(
                place_id=params[place_id], service_id=params[service_id]
            )
        ),
        params=lambda candidate, **params: _events_query(params[locale] or "en"),
        accept=lambda response: response.status_code == 200,
    )


def pick_suggested_place(lookup: Any, address: str, param: str = "address") -> str:
    """The place id an ``address-suggest`` reply resolves ``address`` to.

    The search answers with a list of suggestions. Exactly one ``parcel``
    carrying a ``place_id`` is a single property. A ``place_qualifier`` is a
    multi-dwelling postcode, which needs a house number or property name
    before it resolves to one. ``param`` names the source param the errors
    point the user at.
    """
    lookup.raise_for_status()
    suggestions = lookup.json()

    if not suggestions:
        raise SourceArgumentNotFound(param, address)

    if len(suggestions) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            param, address, [s["name"] for s in suggestions]
        )

    suggestion = suggestions[0]
    if suggestion.get("type") != "parcel" or "place_id" not in suggestion:
        raise SourceArgumentNotFound(
            param,
            address,
            "this looks like a multi-dwelling postcode, please add your house number or property name.",
        )
    return suggestion["place_id"]


def address_suggest_retriever(
    *,
    area: str,
    host: str,
    service_id: str = "waste",
    locale: str = "en",
    address: str = "address",
) -> TwoStepRetriever:
    """Resolve an address through an area's address search, then fetch its events.

    ``area`` and ``service_id`` are the municipality's ReCollect area name and
    service (e.g. ``"StirlingUK"``, ``"waste"``); ``host`` is the member of
    :data:`API_HOSTS` the area lives on, and ``locale`` is sent with both
    requests. ``address`` names the source param holding the address.
    """
    suggest_url = host + SUGGEST_PATH.format(area=area, service_id=service_id)

    def _events_url(place_id: str, **_: Any) -> str:
        path = EVENTS_PATH.format(place_id=place_id, service_id=service_id)
        return f"{host}{path}?{urlencode(_events_query(locale))}"

    return TwoStepRetriever(
        lookup_url=lambda **params: (
            f"{suggest_url}?" + urlencode({"q": params[address], "locale": locale})
        ),
        extract=lambda lookup, source: pick_suggested_place(
            lookup, source.params[address], address
        ),
        schedule_url=_events_url,
    )


class ReCollectEventsParser(Parser["list[tuple[datetime.date, str]]"]):
    """Decode an events reply into ``(date, label)`` rows, pickups only.

    Each event is a day carrying one or more flags. A pickup flag has
    ``event_type == "pickup"``; holidays and notices carry none and are not
    collections. The label is the flag's ``subject``, its display name.
    """

    def __init__(self, place_id: str = "place_id"):
        self._place_id = place_id

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        if response.status_code == 404:
            value = source.params.get(self._place_id) if source else None
            raise SourceArgumentNotFound(
                self._place_id,
                value,
                "no ReCollect place with this place and service ID was found",
            )
        response.raise_for_status()
        events = response.json().get("events")
        response_shape.expect(
            isinstance(events, list),
            source_name=response_shape.source_name(source),
            detail="ReCollect response has no events list",
            raw=response.text,
        )

        rows: list[tuple[datetime.date, str]] = []
        for event in events:
            day = datetime.date.fromisoformat(event["day"])
            for flag in event.get("flags", []):
                if flag.get("event_type") != "pickup":
                    continue
                label = flag.get("subject") or flag.get("name")
                if label:
                    rows.append((day, label))
        return rows
