"""The "hämtningsplanerare" widget of Sitevision municipal sites (FEV, Östersund).

A page such as ``/atervinning/sophamtning.html?q=<address>`` is server-rendered
with the widget's state embedded as
``AppRegistry.registerInitialState('<portlet id>', {...});``. The payload that
carries a ``formAddressText`` key is the fetch planner. It lists one container
per waste type, each with the next pickup (``pickupDateIso``) and the one after
(``nextPickupDateIso``) as UTC instants, or, for an address that is not unique,
a list of ``hits`` to choose from.

:class:`FetchPlannerParser` yields ``(date, waste type)`` rows. Only two
occurrences per container are published, so the interval between them is
measured per container and projected ``count`` times, rather than assuming a
fixed cadence.
"""

import datetime
import json
import re
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

# The portlet id is an implementation detail, so every registered state is
# tried and the planner's is recognised by its ``formAddressText`` key.
_STATE = re.compile(r"registerInitialState\('[^']+',(\{.*?\})\);", re.DOTALL)


def _local_date(iso: str, timezone: ZoneInfo) -> datetime.date:
    instant = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return instant.astimezone(timezone).date()


class FetchPlannerParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, waste type)`` rows from the embedded fetch-planner state.

    Args:
        argument: the config param blamed when the address is unknown.
        count: occurrences projected per container from the published interval.
        timezone: the zone the UTC instants are read in.
    """

    def __init__(
        self,
        argument: str = "address",
        count: int = 12,
        timezone: str = "Europe/Stockholm",
    ):
        self.argument = argument
        self.count = count
        self.timezone = ZoneInfo(timezone)

    def _state(self, text: str) -> "dict[str, Any] | None":
        for match in _STATE.finditer(text):
            try:
                payload = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and "formAddressText" in payload:
                return payload
        return None

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        response.raise_for_status()
        value = source.params.get(self.argument) if source is not None else None
        state = self._state(response.text)
        if state is None:
            raise SourceArgumentNotFound(
                self.argument,
                value,
                message_addition="the schedule page could not be parsed, it may have changed format.",
            )

        containers = state.get("containers") or []
        if not containers:
            hits = state.get("hits") or []
            suggestions = sorted(
                {
                    f"{hit['PickupAddress']}, {hit.get('PickupCity', '').title()}"
                    for hit in hits
                    if hit.get("PickupAddress")
                }
            )
            if suggestions:
                raise SourceArgumentNotFoundWithSuggestions(
                    self.argument, value, suggestions
                )
            raise SourceArgumentNotFound(self.argument, value)

        rows: list[tuple[datetime.date, str]] = []
        for container in containers:
            label = container.get("typeText", "Unknown")
            pickup_iso = container.get("pickupDateIso")
            if not pickup_iso:
                continue
            first = _local_date(pickup_iso, self.timezone)
            next_iso = container.get("nextPickupDateIso")
            interval = 0
            if container.get("hasNextPickup") and next_iso:
                interval = (_local_date(next_iso, self.timezone) - first).days
            if not interval:
                rows.append((first, label))
                continue
            for i in range(self.count):
                rows.append((first + datetime.timedelta(days=interval * i), label))
        return rows
