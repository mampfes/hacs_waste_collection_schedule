"""kiedyodpady.pl (mOdpady / mMieszkaniec): the schedule API behind Polish municipal sites.

Every municipality on the platform has its own site (``<municipality>.kiedyodpady.pl``)
but they all talk to one public JSON API, ``api.kiedyodpady.pl/public``, and the
only thing that tells them apart is the ``Origin`` header of the request. The
address is resolved one level at a time::

    GET  /territory/localities                          [{id, extendedName, ...}]
    GET  /territory/localities/<id>/streets             [{id, extendedName, ...}]
    GET  /territory/localities/<id>/addresses/<street>  ["1", "2a", "pozostałe", ...]
    POST /schedules/find   {from, to, queries: [{localityId, streetId, number, ...}]}
    GET  /waste-types                                   [{id, name, icon, ...}]

The schedule names a waste type only by id (``occurrences[].what``), so the
types list has to be read next to it. :class:`ScheduleRetriever` does the whole
conversation and hands back both responses; :class:`ScheduleParser` joins them
into ``(date, waste type name)`` rows. A source on this platform only declares
which ``municipality`` it is::

    retrieve = Kiedyodpady.ScheduleRetriever()
    parse = Kiedyodpady.ScheduleParser()
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import Lookup, Request, RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

API_URL = "https://api.kiedyodpady.pl/public"
DEFAULT_LOOKAHEAD_DAYS = 365


def _normalize(value: str) -> str:
    return value.strip().lower().casefold()


def _headers(*_: Any, municipality: str, **__: Any) -> dict[str, str]:
    """The API scopes its answer by the ``Origin`` of the municipality's site."""
    return {
        "Origin": f"https://{municipality.strip().lower()}.kiedyodpady.pl",
        "Accept": "application/json",
    }


def _extended_name_id(response: Any, value: str | None, argument: str) -> str:
    """The id of the entry whose ``extendedName`` equals ``value``."""
    entries = response.json()
    target = _normalize(value or "")
    for entry in entries:
        name = entry.get("extendedName", "")
        if name and _normalize(name) == target:
            return entry["id"]
    raise SourceArgumentNotFoundWithSuggestions(
        argument,
        value,
        suggestions=[e["extendedName"] for e in entries if e.get("extendedName")],
    )


def _locality_id(response: Any, *_: Any, city: str, **__: Any) -> str:
    return _extended_name_id(response, city, "city")


def _street_id(response: Any, *keys: Any, street: str, **__: Any) -> str:
    return _extended_name_id(response, street, "street")


def _check_number(response: Any, *_: Any, number: str, **__: Any) -> bool:
    numbers = response.json()
    if number.strip() not in numbers:
        raise SourceArgumentNotFoundWithSuggestions(
            "number", number.strip(), suggestions=numbers
        )
    return True


def _has_street(*_: Any, street: str | None = None, **__: Any) -> bool:
    return bool(street and street.strip())


def _has_number(
    *_: Any, street: str | None = None, number: str | None = None, **__: Any
) -> bool:
    return _has_street(street=street) and bool(number and number.strip())


def _street_url(locality_id: str, *_: Any, **__: Any) -> str:
    return f"{API_URL}/territory/localities/{locality_id}/streets"


def _numbers_url(locality_id: str, street_id: str, *_: Any, **__: Any) -> str:
    return f"{API_URL}/territory/localities/{locality_id}/addresses/{street_id}"


def _query(
    *keys: Any,
    number: str | None = None,
    lookahead_days: int | None = None,
    **__: Any,
) -> dict[str, Any]:
    locality_id, street_id = keys[0], keys[1]
    today = datetime.date.today()
    days = DEFAULT_LOOKAHEAD_DAYS if lookahead_days is None else int(lookahead_days)
    return {
        "from": today.isoformat(),
        "to": (today + datetime.timedelta(days=days)).isoformat(),
        "queries": [
            {
                "localityId": locality_id,
                "streetId": street_id or "",
                "number": (number or "").strip(),
                "propertyType": "",
                "buildingType": "",
            }
        ],
    }


_SCHEDULE = Request(
    f"{API_URL}/schedules/find",
    method="POST",
    json=_query,
    headers=_headers,
    before=(
        Lookup(f"{API_URL}/territory/localities", headers=_headers, pick=_locality_id),
        Lookup(
            _street_url,
            headers=_headers,
            when=_has_street,
            pick=_street_id,
        ),
        Lookup(
            _numbers_url,
            headers=_headers,
            when=_has_number,
            pick=_check_number,
        ),
    ),
)

_WASTE_TYPES = Request(f"{API_URL}/waste-types", headers=_headers)


class ScheduleRetriever(RetrieverFunc):
    """Resolve the address, then fetch the schedule and the waste-type names.

    Returns ``[waste_types_response, schedule_response]`` for
    :class:`ScheduleParser`.
    """

    def __call__(self, source: BaseSource) -> Any:
        schedule = _SCHEDULE(source)
        return [_WASTE_TYPES(source), schedule]


class ScheduleParser:
    """``(date, waste type name)`` rows from :class:`ScheduleRetriever`'s answer."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[datetime.date, str]]:
        types_response, schedule_response = response
        names = {
            item["id"]: item.get("name", item["id"])
            for item in types_response.json()
            if "id" in item
        }
        return [
            (
                datetime.datetime.fromisoformat(occurrence["when"]).date(),
                names.get(occurrence.get("what", ""), occurrence.get("what", "")),
            )
            for occurrence in schedule_response.json().get("occurrences", [])
        ]
