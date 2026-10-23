"""Sector 27 Müllkalender (muellkalender.sector27.de), Kreis Recklinghausen.

The calendar is a Laravel Livewire component (``pickup-calendar``). The page
ships the component's state as a ``wire:snapshot`` and the CSRF token and update
URI on its Livewire ``<script>``; every change (town, year, street) is a POST of
the current snapshot plus the updates, answered with the next snapshot and the
re-rendered calendar HTML. :class:`Sector27Retriever` drives that conversation
for one address and returns one calendar per year; :class:`Sector27Parser`
reads the twelve month grids.

A pickup is only a coloured square, with no text, so the rows carry the
square's ``bg-*`` colour class as their label.
"""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule import lookups, response_shape
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_LOGGER = logging.getLogger(__name__)

URL = "https://muellkalender.sector27.de"
HEADERS = {"user-agent": "Mozilla/5.0"}

#: the town dropdown's ids
CITIES = {
    "Datteln": 9,
    "Marl": 3,
    "Oer-Erkenschwick": 8,
}


class _Livewire:
    """One Livewire component session: the snapshot, re-sent with every update."""

    def __init__(self, source: BaseSource, timeout: int):
        self._session = source.session
        self._timeout = timeout
        r = self._session.get(URL, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        script = soup.find("script", attrs={"data-update-uri": True})
        component = soup.find(attrs={"wire:name": "pickup-calendar"})
        if script is None or component is None:
            raise response_shape.ResponseShapeError(
                response_shape.source_name(source),
                "no Livewire pickup-calendar component on the page",
            )
        self._csrf = str(script["data-csrf"])
        self._update_uri = str(script["data-update-uri"])
        self._snapshot = str(component["wire:snapshot"])

    def update(self, updates: dict | None = None, calls: list | None = None) -> dict:
        r = self._session.post(
            self._update_uri,
            json={
                "_token": self._csrf,
                "components": [
                    {
                        "snapshot": self._snapshot,
                        "updates": updates or {},
                        "calls": calls or [],
                    }
                ],
            },
            headers={**HEADERS, "X-Livewire": "1", "X-CSRF-TOKEN": self._csrf},
            timeout=self._timeout,
        )
        r.raise_for_status()
        component = r.json()["components"][0]
        self._snapshot = component["snapshot"]
        return component["effects"]

    def search_streets(self, search: str) -> list[dict[str, Any]]:
        effects = self.update(
            calls=[
                {
                    "path": "",
                    "method": "callSchemaComponentMethod",
                    "params": [
                        "form.street_id",
                        "getSearchResultsForJs",
                        {"search": search},
                    ],
                }
            ]
        )
        return effects["returns"][0]


def _street_id(livewire: _Livewire, street: str) -> Any:
    """Resolve the street name to its id.

    The search answers at most 50 streets, so the full name is tried first and,
    if it does not match exactly, every word of it, to collect suggestions.
    """
    if not street or not street.strip():
        raise SourceArgumentNotFound("street", street)
    wanted = lookups.normalize_text(street)
    searches = list(dict.fromkeys([street.strip(), *street.split()]))
    suggestions: dict[str, None] = {}
    for search in searches:
        for entry in livewire.search_streets(search):
            name = str(entry.get("label", "")).strip()
            if not name:
                continue
            suggestions[name] = None
            if lookups.normalize_text(name) == wanted:
                return entry["value"]
    if suggestions:
        raise SourceArgumentNotFoundWithSuggestions("street", street, list(suggestions))
    raise SourceArgumentNotFound("street", street)


class Sector27Retriever(RetrieverFunc):
    """``[(year, calendar html), ...]`` for the configured town and street.

    The current year always; from ``rollover_month`` the next year too.
    """

    def __init__(
        self,
        *,
        city: str = "city",
        street: str = "street",
        rollover_month: int = 9,
        timeout: int = 30,
    ):
        self._city = city
        self._street = street
        self._rollover_month = rollover_month
        self._timeout = timeout

    def __call__(self, source: BaseSource) -> Any:
        town = source.params.get(self._city)
        if town not in CITIES:
            raise SourceArgumentNotFoundWithSuggestions("city", town, list(CITIES))
        now = datetime.datetime.now()

        livewire = _Livewire(source, self._timeout)
        livewire.update({"data.city_id": CITIES[town], "data.year": now.year})
        street_id = _street_id(livewire, source.params.get(self._street) or "")
        calendars = [(now.year, livewire.update({"data.street_id": street_id})["html"])]
        if now.month >= self._rollover_month:
            calendars.append(
                (now.year + 1, livewire.update({"data.year": now.year + 1})["html"])
            )
        return calendars


class Sector27Parser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, colour class)`` rows of every calendar the retriever returned."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[datetime.date, str]]:
        rows: list[tuple[datetime.date, str]] = []
        for year, html in response:
            soup = BeautifulSoup(html, "html.parser")
            months = soup.select("div.grid.grid-cols-7")
            response_shape.expect(
                len(months) == 12,
                source_name=response_shape.source_name(source),
                detail=f"expected 12 month grids, found {len(months)}",
                raw=html,
            )
            for month, grid in enumerate(months, start=1):
                for cell in grid.find_all("div", class_="flex-col", recursive=False):
                    day = next(
                        (
                            int(child.get_text(strip=True))
                            for child in cell.find_all("div", recursive=False)
                            if child.get_text(strip=True).isdigit()
                        ),
                        None,
                    )
                    pickups = cell.find("div", class_="min-h-10")
                    if day is None or pickups is None:
                        continue
                    for marker in pickups.find_all("div", recursive=False):
                        colour = next(
                            (c for c in marker.get("class", []) if c.startswith("bg-")),
                            None,
                        )
                        if colour is not None:
                            rows.append((datetime.date(year, month, day), colour))
        return rows
