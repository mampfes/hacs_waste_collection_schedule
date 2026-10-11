"""Publidata waste-collection services (``api.publidata.io`` / ``api.publidata.ca``).

Publidata runs the waste widgets of French and Quebec municipalities and
syndicates. Both hosts speak the same protocol::

    GET /v2/geocoder?q=<address>[&citycode=<INSEE>]&limit=10&lookup=publidata
        -> [{"data": {"features": [{"geometry": {"coordinates": [..]},
                                    "properties": {"id": <address id>}}]}}]
    GET /v2/search?types[]=Platform::Services::WasteCollection
                  &collection_modes[]=truck&address_id=<id>[&instances[]=<id>]
        -> {"hits": {"hits": [{"_source": {"metas": {"garbage_types": ["omr"],
                                                     "sectorization": "single"},
                                           "schedules": [...]}}]}}

A schedule is not a list of dates but an OpenStreetMap-style ``opening_hours``
expression between ``start_at`` and ``end_at`` (``week 2-52/2 Mo 12:00-17:00``,
``2025 Jan,Apr Tu[1]``, ``Jan 01-Mar 14 off "Fermeture"``). A ``regular`` or
``exception`` schedule adds collections, a ``closed`` or ``closing_exception``
one removes them.

:func:`calendar_retriever` geocodes the address and fetches the search result,
:class:`ScheduleExpander` turns the schedules into ``(date, garbage type)`` rows
and :data:`TYPE_MAP` maps the garbage types to waste types.
"""

from __future__ import annotations

import calendar
import logging
import re
from collections.abc import Iterable, Iterator
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from dateutil.rrule import (
    DAILY,
    FR,
    MO,
    MONTHLY,
    SA,
    SU,
    TH,
    TU,
    WE,
    WEEKLY,
    rrule,
    rruleset,
)

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import Preprocessor
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_LOGGER = logging.getLogger(__name__)

TYPE_MAP = {
    "omr": wt.GENERAL_WASTE,
    "emb": wt.RECYCLABLES,
    "enc": wt.BULKY_WASTE,
    "dv": wt.GARDEN_WASTE,
    "bio": wt.ORGANIC,
    "verre": wt.GLASS,
    "sapin": wt.OTHER,
    "jrm": wt.PAPER,
}

_WEEKDAYS = {"Mo": MO, "Tu": TU, "We": WE, "Th": TH, "Fr": FR, "Sa": SA, "Su": SU}
_MONTHS = [m for m in calendar.month_abbr if m]
_TIMESTAMP = "%Y-%m-%dT%H:%M:%S.%f%z"


# --- retrieval -------------------------------------------------------------


def _address_id(response, *_, address, **__) -> dict:
    results = response.json()
    features = (results[0].get("data", {}).get("features", [])) if results else []
    if not features:
        raise SourceArgumentNotFound("address", address)
    lat, lon = features[0]["geometry"]["coordinates"]
    return {"lat": lat, "lon": lon, "address_id": features[0]["properties"]["id"]}


def calendar_retriever(host: str) -> LookupChainRetriever:
    """The search result of the ``address`` (and ``insee_code``, ``instance_id``,
    ``public_type``) params on ``api.<host>``.

    ``insee_code``, ``instance_id`` and ``public_type`` are optional: the Canadian
    host takes the address alone.
    """
    api = f"https://api.{host}/v2"
    return LookupChainRetriever(
        steps=(
            Lookup(
                f"{api}/geocoder",
                params=lambda address, insee_code=None, **_: {
                    "q": address,
                    "limit": 10,
                    "lookup": "publidata",
                    **({"citycode": insee_code} if insee_code else {}),
                },
                pick=_address_id,
            ),
        ),
        url=f"{api}/search",
        params=lambda located, instance_id=None, public_type=None, **_: {
            "size": 999,
            "types[]": "Platform::Services::WasteCollection",
            "collection_modes[]": "truck",
            **({"instances[]": int(instance_id)} if instance_id else {}),
            **(located if instance_id else {"address_id": located["address_id"]}),
            **(
                {"publics[]": "resident", "public_types[]": public_type}
                if public_type
                else {}
            ),
        },
        raise_for_status=True,
    )


# --- opening_hours ---------------------------------------------------------


def _weekdays(text: str) -> dict:
    """``Mo``, ``Tu[2]``, ``We[2,4]`` or ``We,Th,Fr``."""
    days: list[Any] = []
    for name, nth in re.findall(r"([A-Za-z]{2})(?:\[(\d+(?:,\d+)*)\])?", text):
        if nth:
            days.extend(_WEEKDAYS[name](int(n)) for n in nth.split(","))
        else:
            days.append(_WEEKDAYS[name])
    if not days:
        raise ValueError(f"Invalid day format: {text}")
    return {"byweekday": days}


def _months(text: str) -> dict:
    text = text.replace(":", "")  # seen in production: "Dec:"
    months: list[int] = []
    for item in text.split(","):  # "Feb,May", "Sep-Nov" or "May-Jul,Oct"
        first, _, last = item.partition("-")
        months.extend(
            range(
                _MONTHS.index(first) + 1,
                _MONTHS.index(last or first) + 2,
            )
        )
    return {"bymonth": months}


def _years(text: str) -> dict:
    if "-" in text:
        first, last = (int(y) for y in text.split("-"))
    elif "," in text:
        years = [int(y) for y in text.split(",")]
        if years != list(range(min(years), max(years) + 1)):
            raise ValueError(f"Invalid year range: {text}")
        first, last = min(years), max(years)
    else:
        first = last = int(text)
    return {
        "dtstart": datetime(first, 1, 1, tzinfo=UTC),
        "until": datetime(last, 12, 31, tzinfo=UTC),
    }


def _part(part: str) -> dict:
    if re.match(r"^\d{4}", part):
        return _years(part)
    if any(month in part for month in _MONTHS):
        return _months(part)
    if any(day in part for day in _WEEKDAYS):
        return _weekdays(part)
    if re.match(r"^(\d{1,2})([,-]\d{1,2})*$", part):
        return {"bymonthday": [int(d) for d in re.split("[,-]", part)]}
    if re.match(r"^(\d{2}:\d{2})|(24/7)", part):
        return {}  # the time of day is not used
    raise ValueError(f"Invalid part: {part}")


def _week_numbers(text: str) -> dict:
    """``2-52/2``, ``1-17,19-52`` or ``18``."""
    weeks: list[int] = []
    for item in text.split(","):
        if "-" not in item:
            weeks.append(int(item))
            continue
        first, rest = item.split("-")
        last, _, step = rest.partition("/")
        weeks.extend(range(int(first), int(last) + 1, int(step or 1)))
    return {"byweekno": weeks}


_RANGE = (
    r"^(\d{4} \w+ \d{1,2}-\d{4} \w+ \d{1,2})(.*)",  # 2024 Jan 01-2024 May 12
    r"^(\w+ \d{1,2}-\w+ \d{1,2})(.*)",  # Jan 01-Mar 14
)


def _date_range(text: str, default_year: int) -> tuple[dict, str] | None:
    for pattern in _RANGE:
        match = re.search(pattern, text)
        if not match:
            continue
        first, last = match.group(1).split("-")
        if re.match(r"^\d{4} ", first):
            start = datetime.strptime(first + " +0000", "%Y %b %d %z")
            end = datetime.strptime(last + " +0000", "%Y %b %d %z")
        else:
            start = datetime.strptime(f"{default_year} {first} +0000", "%Y %b %d %z")
            end = datetime.strptime(f"{default_year} {last} +0000", "%Y %b %d %z")
        return {"dtstart": start, "until": end}, match.group(2).strip()
    return None


def _rule(schedule: dict, now: datetime) -> rrule:
    start = (
        datetime.strptime(schedule["start_at"], _TIMESTAMP)
        if schedule.get("start_at")
        else None
    )
    # Publidata disregards ``end_at`` of a regular schedule.
    if schedule.get("end_at") and schedule["schedule_type"] != "regular":
        end = datetime.strptime(schedule["end_at"], _TIMESTAMP)
    else:
        end = now + timedelta(days=365)
    text = schedule["opening_hours"]
    kwargs: dict[str, Any] = {"freq": MONTHLY, "dtstart": start, "until": end}

    ranged = _date_range(text, start.year if start else now.year)
    if ranged:
        kwargs.update(ranged[0])
        text = ranged[1]

    parts = text.split()
    has_rule = False
    while parts:
        part = parts.pop(0)
        if part == "week":
            kwargs["freq"] = WEEKLY
            kwargs.update(_week_numbers(parts.pop(0)))
            has_rule = True
        elif part.startswith(("off", '"')):
            continue  # the schedule type says it is a closure; or a comment
        else:
            kwargs.update(_part(part))
            has_rule = True

    # A bare range ('Nov 29-Dec 31 off "Fermeture"') covers every day of it.
    if not has_rule and ranged:
        kwargs["freq"] = DAILY
    return rrule(**kwargs)


def _listed_dates(text: str) -> list[datetime]:
    """``2025 Jan 17,2026 Jan 16 06:00-23:59``: Publidata's malformed date list."""
    pattern = (
        r"^(?:\d{4} [A-Za-z]{3} \d{1,2})(?:,\d{4} [A-Za-z]{3} \d{1,2})+"
        r"(?: \d{2}:\d{2}-\d{2}:\d{2})?$"
    )
    if not text or not re.match(pattern, text.strip()):
        return []
    return [
        datetime.strptime(token + " +0000", "%Y %b %d %z")
        for token in re.findall(r"\d{4} [A-Za-z]{3} \d{1,2}", text)
    ]


_ADDS = ("regular", "exception")
_REMOVES = ("closed", "closing_exception")


def collection_dates(
    schedules: Iterable[dict], now: datetime | None = None
) -> Iterator[date]:
    """The dates a garbage type's schedules produce (pure)."""
    now = now or datetime.now(UTC)
    rules = rruleset()
    for schedule in schedules:
        kind = schedule.get("schedule_type")
        try:
            rule = _rule(schedule, now)
            if kind in _ADDS:
                rules.rrule(rule)
            elif kind in _REMOVES:
                rules.exrule(rule)
            continue
        except Exception as err:
            listed = _listed_dates(schedule.get("opening_hours", ""))
            if listed and kind in _ADDS:
                for moment in listed:
                    rules.rdate(moment)
                continue
            if listed and kind in _REMOVES:
                for moment in listed:
                    rules.exdate(moment)
                continue
            _LOGGER.warning(
                "Skipping invalid Publidata schedule id=%s opening_hours=%r: %s",
                schedule.get("id"),
                schedule.get("opening_hours"),
                err,
            )
    for moment in rules:
        yield moment.date()


def _schedules_by_type(hits: list[dict]) -> dict[str, list[dict]]:
    def group(sources: Iterable[dict]) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = {}
        for source in sources:
            types = (source.get("metas") or {}).get("garbage_types") or []
            if types and types[0]:
                grouped.setdefault(types[0], []).extend(source.get("schedules") or [])
        return grouped

    sources = [hit.get("_source", {}) for hit in hits]
    single = [
        s for s in sources if (s.get("metas") or {}).get("sectorization") == "single"
    ]
    # Some instances only report "multi" hits for an address: use every hit.
    return group(single) or group(sources)


class ScheduleExpander(Preprocessor[Any, "tuple[date, str]"]):
    """Expand a Publidata search result into ``(date, garbage type)`` rows."""

    def __call__(
        self, records: Any, source: BaseSource | None = None
    ) -> Iterator[tuple[date, str]]:
        hits = ((records or {}).get("hits") or {}).get("hits") or []
        for garbage_type, schedules in _schedules_by_type(hits).items():
            for day in collection_dates(schedules):
                yield day, garbage_type
