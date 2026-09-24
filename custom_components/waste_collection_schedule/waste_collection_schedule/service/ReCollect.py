"""ReCollect (Routeware) platform: the JSON events API behind its widgets.

ReCollect also publishes each place's schedule as an ``.ics`` export, which the
generic ICS source reads (``doc/ics/yaml/recollect.yaml``). This module is the
JSON side of the same data, for when that export is unavailable: the events
endpoint takes the same ``place_id`` and ``service_id`` as the ICS link.

A place lives on exactly one of two hosts (North America or Europe); the other
answers 404. :func:`events_retriever` tries both in turn, and
:class:`ReCollectEventsParser` turns the reply into ``(date, label)`` rows,
keeping pickups and dropping holiday and notice flags.
"""

import datetime
from typing import TYPE_CHECKING, Any

from waste_collection_schedule import response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import FirstMatchRetriever

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

API_HOSTS = ("https://api.recollect.net", "https://api.eu.recollect.net")
EVENTS_PATH = "/api/places/{place_id}/services/{service_id}/events"

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


def events_retriever(
    place_id: str = "place_id", service_id: str = "service_id", locale: str = "locale"
) -> FirstMatchRetriever:
    """The events request, tried on each ReCollect host until one serves it.

    The arguments name the source's params holding each value. The window runs
    from 30 days back to a year ahead, the same span the widget shows.
    """

    def _params(candidate: str, **params: Any) -> dict[str, str]:
        today = datetime.date.today()
        return {
            "hide": "reminder_only",
            "after": (today - datetime.timedelta(days=30)).isoformat(),
            "before": (today + datetime.timedelta(days=365)).isoformat(),
            "locale": params[locale] or "en",
        }

    return FirstMatchRetriever(
        candidates=API_HOSTS,
        url=lambda candidate, **params: (
            candidate
            + EVENTS_PATH.format(
                place_id=params[place_id], service_id=params[service_id]
            )
        ),
        params=_params,
        accept=lambda response: response.status_code == 200,
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
