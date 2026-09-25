"""EDP Future "SimpleWastePickup" (Sweden): the pipeline components.

Many Swedish municipalities and waste companies publish their collection days
through the same EDP Future web module, each on its own host and path, e.g.
``https://future.molndal.se/FutureWeb/SimpleWastePickup``. It has two endpoints:

* ``SearchAdress`` (POST ``searchText``) answers
  ``{"Succeeded": true, "Buildings": ["Storgatan 12, Huskvarna (16915)", ...]}``;
* ``GetWastePickupSchedule`` (GET ``address``) takes one of those building
  strings, or just its ``(id)``, and answers ``{"RhServices": [...]}``, one
  entry per bin with only its *next* pickup.

The next pickup comes in three shapes: an ISO date (``2026-10-06``), an ISO
week with month and year for services planned by the week (``v41 Okt 2026``,
sludge and grease traps), or a month and year (``Feb 2027``). When it is empty
the frequency sometimes names the week instead (``Vecka 27``).

``EdpFutureWebRetriever`` resolves the address and returns the schedule
response; ``EdpFutureWebParser`` reads it into ``{date, type, frequency,
container}`` records. ``TYPE_VALUE_MAP`` holds the bin labels the platform's
deployments share, for a source's ``type_value_map`` to spread.
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from waste_collection_schedule import response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentException,
    SourceArgumentNotFound,
)

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

# Labels shared across deployments. The four-compartment bins ("fyrfack") are
# numbered: bin 1 holds the residual and food waste, bin 2 the recyclables.
TYPE_VALUE_MAP: dict[str, wt.WasteType] = {
    "Kärl 1": wt.GENERAL_WASTE,
    "Kärl 2": wt.RECYCLABLES,
    "FNI1": wt.GENERAL_WASTE,
    "FNI2": wt.RECYCLABLES,
    "FNI Kärl 1": wt.GENERAL_WASTE,
    "FNI Kärl 2": wt.RECYCLABLES,
    "Fyrfack 1": wt.GENERAL_WASTE,
    "Fyrfack 2": wt.RECYCLABLES,
    "Fyrfackskärl 1": wt.GENERAL_WASTE,
    "Fyrfackskärl 2": wt.RECYCLABLES,
    "Restavfall": wt.GENERAL_WASTE,
    "Hushåll": wt.GENERAL_WASTE,
    "Brännbart": wt.GENERAL_WASTE,
    "Deponi": wt.GENERAL_WASTE,
    "Matavfall": wt.FOOD_WASTE,
    "Matavfall tätt": wt.FOOD_WASTE,
    "Mat": wt.FOOD_WASTE,
    "Trädgårdsavfall": wt.GARDEN_WASTE,
    "Förpackningar": wt.RECYCLABLES,
    "Returmaterial": wt.RECYCLABLES,
    "Plastförp.": wt.RECYCLABLES,
    "Metallförp.": wt.RECYCLABLES,
    "Pappersförp.": wt.PAPER,
    "Tidningar": wt.PAPER,
    "Glasförp.färg": wt.GLASS,
    "Glasförp.ofärg": wt.GLASS,
    # Danderyd's combined containers: two streams in one label.
    "Glas/Glas/Metal": [wt.GLASS, wt.RECYCLABLES],
    "Papper/Plast": [wt.PAPER, wt.RECYCLABLES],
    "Batterier": wt.HAZARDOUS,
    # Emptying a septic tank or a grease trap: a real visit, but no bin.
    "Slam": wt.OTHER,
    "Fett": wt.OTHER,
}

_BUILDING_ID_RE = re.compile(r"\((\d+)\)\s*$")
_WEEK_RE = re.compile(r"^v(?:ecka)?\s*(\d{1,2})\b", re.IGNORECASE)
_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "maj": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "okt": 10,
    "nov": 11,
    "dec": 12,
}


class EdpFutureWebRetriever:
    """Resolve an address to its ``GetWastePickupSchedule`` response.

    Args:
        base_url: the deployment's ``.../SimpleWastePickup`` URL, or a
            ``callable(**source.params) -> str`` for a source serving several
            deployments (raise a ``SourceArgument*`` exception there for a
            value that names none).
        address: ``source.params`` field with the street address, or ``None``
            for a source configured by building id only. An address ending in
            ``(<digits>)``, as the provider's own search lists it, is used as
            the building id without searching.
        building_id: ``source.params`` field carrying the building id
            directly; takes precedence over the address when set.
        search_text: ``callable(**source.params) -> str`` shaping the search
            text (e.g. dropping a locality the source reads itself).
        exact_match: several search hits are disambiguated by an exact (case-
            and space-insensitive) match against the address instead of taking
            the first; an inconclusive match raises
            ``SourceArgAmbiguousWithSuggestions``.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str | Callable[..., str],
        *,
        address: str | None = "street_address",
        building_id: str | None = None,
        search_text: Callable[..., str] | None = None,
        exact_match: bool = False,
        timeout: int = 30,
    ):
        self.base_url = base_url
        self.address = address
        self.building_id = building_id
        self.search_text = search_text
        self.exact_match = exact_match
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> Response:
        base_url = (
            self.base_url(**source.params) if callable(self.base_url) else self.base_url
        ).rstrip("/")
        response = source.session.get(
            f"{base_url}/GetWastePickupSchedule",
            params={"address": self._address(source, base_url)},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response

    def _address(self, source: BaseSource, base_url: str) -> str:
        direct = self.building_id and source.params.get(self.building_id)
        if direct:
            return f"({str(direct).strip().strip('()')})"
        assert self.address is not None, "no address and no building id field"
        address = str(source.params.get(self.address) or "").strip()
        match = _BUILDING_ID_RE.search(address)
        if match:
            return f"({match.group(1)})"
        text = self.search_text(**source.params) if self.search_text else address
        return self._select(address, self._search(source, base_url, text))

    def _search(self, source: BaseSource, base_url: str, text: str) -> list[str]:
        response = source.session.post(
            f"{base_url}/SearchAdress",
            data={"searchText": text},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        assert self.address is not None
        if not data.get("Succeeded"):
            raise SourceArgumentException(
                self.address, f"The provider could not search for {text!r}."
            )
        return list(data.get("Buildings") or [])

    def _select(self, address: str, buildings: list[str]) -> str:
        assert self.address is not None
        if not buildings:
            raise SourceArgumentNotFound(self.address, address)
        if not self.exact_match or len(buildings) == 1:
            return buildings[0]

        def normalise(text: str) -> str:
            return re.sub(r"[\s,]", "", _BUILDING_ID_RE.sub("", text)).lower()

        wanted = normalise(address)
        exact = [b for b in buildings if normalise(b) == wanted]
        if len(exact) == 1:
            return exact[0]
        raise SourceArgAmbiguousWithSuggestions(
            self.address, address, exact or buildings
        )


class EdpFutureWebParser:
    """Read ``RhServices`` into ``{date, type, frequency, container}`` records.

    Entries with no readable next pickup are skipped, and the same bin type on
    the same day is reported once (a property often has several bins of one
    type, each listed separately).
    """

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        data = response.json()
        response_shape.expect(
            isinstance(data, dict) and isinstance(data.get("RhServices"), list),
            source_name=response_shape.source_name(source),
            detail="EDP Future response has no 'RhServices' list",
            raw=response.text,
        )
        records: list[dict[str, Any]] = []
        seen: set[tuple[datetime.date, str]] = set()
        for item in data["RhServices"]:
            waste_type = (item.get("WasteType") or "").strip()
            frequency = (item.get("WastePickupFrequency") or "").strip()
            pickup = parse_pickup(item.get("NextWastePickup") or "") or parse_pickup(
                frequency
            )
            if pickup is None or not waste_type or (pickup, waste_type) in seen:
                continue
            seen.add((pickup, waste_type))
            bin_type = item.get("BinType") or {}
            records.append(
                {
                    "date": pickup,
                    "type": waste_type,
                    "frequency": frequency,
                    "container": bin_type.get("ContainerType"),
                }
            )
        return records


def parse_pickup(text: str) -> datetime.date | None:
    """Read a next-pickup value; ``None`` when it names no date.

    ``2026-10-06`` is that day; ``v41 Okt 2026`` and ``Vecka 41`` are the
    Monday of ISO week 41 (of the stated year, else of the current one, or the
    next if that week has passed); ``Feb 2027`` is the first of the month.
    """
    text = text.strip()
    if not text:
        return None
    try:
        return datetime.date.fromisoformat(text[:10])
    except ValueError:
        pass

    parts = text.split()
    week = _WEEK_RE.match(text)
    if week:
        years = [int(p) for p in parts if p.isdigit() and len(p) == 4]
        if years:
            return datetime.date.fromisocalendar(years[0], int(week.group(1)), 1)
        today = datetime.date.today()
        monday = datetime.date.fromisocalendar(today.year, int(week.group(1)), 1)
        if monday + datetime.timedelta(days=6) < today:
            monday = datetime.date.fromisocalendar(
                today.year + 1, int(week.group(1)), 1
            )
        return monday

    if len(parts) == 2 and parts[1].isdigit():
        month = _MONTHS.get(parts[0][:3].lower())
        if month:
            return datetime.date(int(parts[1]), month, 1)
    return None
