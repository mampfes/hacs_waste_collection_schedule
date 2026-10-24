"""Geovest (geovest.bluemilk.dev) collection calendars.

A lookup is one device's favourites:

1. ``GET /api/addresses`` searches a town for the street.
2. The matching address is stored as that device's only favourite
   (``POST /api/favourites/store``), which answers the calendar id. Any
   favourite already on the device is deleted first.
3. ``GET /api/calendar/<id>/week/<date>`` is read once per week of the
   requested window.

:class:`GeovestRetriever` returns those week payloads.
:class:`GeovestParser` reads them into ``(date, category name)`` rows.
"""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_URL = "https://geovest.bluemilk.dev"
_USER_AGENT = "okhttp/4.9.2"
_WEEKDAYS = {"LUN": 0, "MAR": 1, "MER": 2, "GIO": 3, "VEN": 4, "SAB": 5, "DOM": 6}


class _Weeks:
    """A response stand-in carrying the week payloads and the window end."""

    status_code = 200

    def __init__(self, weeks: list[dict[str, Any]], until: date):
        self._payload = {"weeks": weeks, "until": until.isoformat()}

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        """Nothing to raise: every request was checked while following the chain."""


def _town_id(value: Any) -> str:
    normalized = str(value).strip()
    if "-" in normalized:
        normalized = normalized.split("-", 1)[0].strip()
    if not normalized.isdigit():
        raise SourceArgumentNotFound(
            "town_id",
            value,
            "Select the town ID from the dropdown.",
        )
    return normalized


def _days(value: Any) -> int:
    try:
        days = int(value)
    except (TypeError, ValueError):
        raise SourceArgumentNotFound(
            "days",
            value,
            "Enter a positive number of days to fetch.",
        ) from None
    if days < 1:
        raise SourceArgumentNotFound(
            "days",
            value,
            "Enter a positive number of days to fetch.",
        )
    return days


def _headers(authorization: str, *, json_body: bool) -> dict[str, str]:
    headers = {"user-agent": _USER_AGENT}
    if json_body:
        headers["accept"] = "application/json"
        headers["content-type"] = "application/json"
    if authorization:
        headers["authorization"] = authorization
    return headers


def _calendar_id(payload: dict[str, Any]) -> int | None:
    for fav in payload.get("favs", []):
        value = fav.get("value") or {}
        calendar_id = value.get("calendar_id")
        if calendar_id is not None:
            return int(calendar_id)
    return None


def _collection_date(
    week_start: datetime, day_of_month: int, weekday_code: str
) -> date | None:
    possible: list[date] = []
    for month_offset in (-1, 0, 1):
        month = week_start.month + month_offset
        year = week_start.year
        if month < 1:
            month += 12
            year -= 1
        elif month > 12:
            month -= 12
            year += 1
        try:
            candidate = datetime(year, month, day_of_month)
        except ValueError:
            continue
        if abs((candidate - week_start).days) <= 10:
            possible.append(candidate.date())

    if not possible:
        weekday_target = _WEEKDAYS.get(weekday_code)
        if weekday_target is None:
            return None
        delta_days = (weekday_target - week_start.weekday()) % 7
        return (week_start + timedelta(days=delta_days)).date()

    if len(possible) == 1:
        return possible[0]

    weekday_target = _WEEKDAYS.get(weekday_code)
    if weekday_target is not None:
        for found in possible:
            if found.weekday() == weekday_target:
                return found
    return possible[0]


def _week_rows(week: dict[str, Any]) -> list[tuple[date, str]]:
    wastes = week.get("wastes") or {}
    week_start_raw = week.get("from")
    if not week_start_raw:
        return []
    try:
        week_start = datetime.strptime(str(week_start_raw).split(" ")[0], "%Y-%m-%d")
    except ValueError:
        return []

    rows: list[tuple[date, str]] = []
    for day_key, day_wastes in wastes.items():
        if not day_wastes:
            continue
        parts = str(day_key).split("_", 1)
        if len(parts) != 2:
            continue
        try:
            day_of_month = int(parts[0])
        except ValueError:
            continue
        collection_date = _collection_date(week_start, day_of_month, parts[1])
        if collection_date is None:
            continue
        for waste in day_wastes:
            category = waste.get("category_name") or ""
            rows.append((collection_date, category))
    return rows


class GeovestRetriever:
    """The week payloads for ``source.params["address_name"]`` in a town.

    Args:
        timeout: request timeout in seconds.
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def _get(
        self,
        source: BaseSource,
        path: str,
        *,
        params: dict[str, str] | None,
        json_body: bool,
    ) -> Any:
        kwargs: dict[str, Any] = {}
        if params:
            kwargs["params"] = params
        response = source.session.get(
            f"{_URL}{path}",
            headers=_headers(source.params["authorization"], json_body=json_body),
            timeout=self.timeout,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    def _post(
        self,
        source: BaseSource,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        data: str | None = None,
    ) -> Any:
        kwargs: dict[str, Any] = {}
        if params:
            kwargs["params"] = params
        if json_body is not None:
            kwargs["json"] = json_body
        if data is not None:
            kwargs["data"] = data
        response = source.session.post(
            f"{_URL}{path}",
            headers=_headers(source.params["authorization"], json_body=True),
            timeout=self.timeout,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    def _choose(self, addresses: list[dict[str, Any]], source: BaseSource) -> int:
        suggestions = [
            address.get("label") for address in addresses if address.get("label")
        ]
        if len(addresses) == 1:
            return int(addresses[0]["value"])
        number = str(source.params["numbers"]).strip()
        for address in addresses:
            label = (address.get("label") or "").lower()
            if number and re.search(rf"\b{re.escape(number)}\b", label):
                return int(address["value"])
        raise SourceArgAmbiguousWithSuggestions(
            "address_name", source.params["address_name"], suggestions
        )

    def __call__(self, source: BaseSource) -> _Weeks:
        town_id = _town_id(source.params["town_id"])
        address_name = str(source.params["address_name"]).strip()
        calendar_type_id = str(source.params["calendar_type_id"]).strip()
        if calendar_type_id not in {"1", "2"}:
            raise SourceArgumentNotFound(
                "calendar_type_id",
                source.params["calendar_type_id"],
                "Use 1 for private addresses or 2 for businesses.",
            )
        days = _days(source.params["days"])
        device_id = str(source.params.get("device_id") or "").strip()
        if not device_id:
            device_id = uuid.uuid4().hex[:16]

        found = self._get(
            source,
            "/api/addresses",
            params={"filter[name]": address_name, "filter[town_id]": town_id},
            json_body=False,
        )
        addresses = found.get("addresses") or []
        if not addresses:
            raise SourceArgumentNotFound("address_name", address_name)
        address_id = self._choose(addresses, source)

        existing = self._get(
            source,
            "/api/favourites",
            params={"device_id": device_id},
            json_body=True,
        )
        for fav in existing.get("favs", []):
            fav_id = fav.get("key")
            if fav_id is None:
                continue
            self._post(
                source,
                "/api/favourites/delete",
                params={"id": str(fav_id), "device_id": device_id},
                data="",
            )

        stored = self._post(
            source,
            "/api/favourites/store",
            json_body={
                "town_id": town_id,
                "address_id": address_id,
                "calendar_type_id": calendar_type_id,
                "user_id": None,
                "device_id": device_id,
            },
        )
        if stored.get("status") != "ok":
            raise SourceArgumentNotFound(
                "address_name",
                address_name,
                "Unable to create a Geovest schedule entry for this address.",
            )
        calendar_id = _calendar_id(stored)
        if calendar_id is None:
            calendar_id = _calendar_id(
                self._get(
                    source,
                    "/api/favourites",
                    params={"device_id": device_id},
                    json_body=True,
                )
            )
        if calendar_id is None:
            raise SourceArgumentNotFound(
                "address_name",
                address_name,
                "Could not determine a Geovest collection calendar for this address.",
            )

        today = datetime.now()
        end = today + timedelta(days=days)
        weeks: list[dict[str, Any]] = []
        current = today
        while current <= end:
            date_str = f"{current.year}-{current.month}-{current.day}"
            weeks.append(
                self._get(
                    source,
                    f"/api/calendar/{calendar_id}/week/{date_str}",
                    params=None,
                    json_body=False,
                )
            )
            current += timedelta(days=7)
        return _Weeks(weeks, end.date())


class GeovestParser:
    """``(date, category name)`` rows from the week payloads, inside the window."""

    def __call__(
        self, response: _Weeks, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        payload = response.json()
        until = date.fromisoformat(payload["until"])
        rows = [row for week in payload["weeks"] for row in _week_rows(week)]
        return sorted((row for row in rows if row[0] <= until), key=lambda row: row[0])
