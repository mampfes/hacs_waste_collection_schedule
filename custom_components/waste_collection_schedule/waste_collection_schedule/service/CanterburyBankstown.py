"""Published Canterbury-Bankstown address rules and web-app cycle anchor."""

import datetime
import gzip
import json
import re
from collections.abc import Callable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule import recurrence
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.preprocessors import Schedule

STREET_TYPES = {
    "AV": "AVENUE",
    "AVE": "AVENUE",
    "BVD": "BOULEVARD",
    "BLVD": "BOULEVARD",
    "CCT": "CIRCUIT",
    "CL": "CLOSE",
    "CR": "CRESCENT",
    "CRES": "CRESCENT",
    "CT": "COURT",
    "DR": "DRIVE",
    "ESP": "ESPLANADE",
    "GDNS": "GARDENS",
    "GR": "GROVE",
    "GRV": "GROVE",
    "HWY": "HIGHWAY",
    "LN": "LANE",
    "PDE": "PARADE",
    "PKWY": "PARKWAY",
    "PL": "PLACE",
    "RD": "ROAD",
    "RSE": "RISE",
    "SQ": "SQUARE",
    "ST": "STREET",
    "TCE": "TERRACE",
    "WY": "WAY",
}

_STATE = "NSW"

_STATE_SPELLED_OUT = "NEW SOUTH WALES"


def _normalise(value: str) -> str:
    """Compare-ready form: upper case, no commas or slashes, no state."""
    text = value.upper().replace(",", " ").replace("/", " ")
    text = " ".join(text.split()).replace(_STATE_SPELLED_OUT, _STATE)
    words = [STREET_TYPES.get(word, word) for word in text.split()]
    return " ".join(word for word in words if word != _STATE)


ZONE_A = "A"

ZONE_B = "B"

ZONE_WEEKLY = "Weekly"

STANDARD_RESIDENTIAL = "1"

DUAL_COLLECTION = "2a"

DUAL_COLLECTION_ALT = "2b"

INDEPENDENT_YELLOW_ZONE = "2c"

COMBINED_RED_YELLOW = "3"

DUAL_COLLECTION_VARIANT = "4"

MULTI_UNIT_BUILDING = "5"

LARGE_COMPLEX = "6"

_TAB_REGISTRY: dict[str, Callable[[dict], list[tuple | None]]] = {}

_RULE_REGISTRY: dict[str, Callable[..., None]] = {}


def _tab(tab_id: str):

    def decorator(func):
        _TAB_REGISTRY[tab_id] = func
        return func

    return decorator


def _rule(func):
    rule_type = func.__name__.removeprefix("_")
    _RULE_REGISTRY[rule_type] = func
    return func


def _rule_weekly(day: str | None, color: str) -> tuple | None:
    return ("weekly", day, color) if day else None


def _rule_alternating(
    day: str | None, zone_a_even: str, zone_a_odd: str
) -> tuple | None:
    return ("alternating", day, zone_a_even, zone_a_odd) if day else None


def _rule_even_only(day: str | None, color: str) -> tuple | None:
    return ("even_only", day, color) if day else None


def _rule_odd_only(day: str | None, color: str) -> tuple | None:
    return ("odd_only", day, color) if day else None


@_tab(STANDARD_RESIDENTIAL)
def _standard_residential(entry: dict) -> list[tuple | None]:
    return [
        _rule_weekly(entry.get("redServiceDay"), "red"),
        _rule_alternating(entry.get("yellowServiceDay"), "yellow", "green"),
    ]


@_tab(DUAL_COLLECTION)
def _dual_collection(entry: dict) -> list[tuple | None]:
    return [
        _rule_weekly(entry.get("redServiceDay"), "red"),
        _rule_weekly(entry.get("yellowServiceDay"), "yellow"),
        _rule_weekly(entry.get("greenServiceDay"), "green"),
    ]


@_tab(DUAL_COLLECTION_ALT)
def _dual_collection_alt(entry: dict) -> list[tuple | None]:
    return [
        _rule_weekly(entry.get("redServiceDay"), "red"),
        _rule_weekly(entry.get("redServiceDay2"), "red"),
        _rule_alternating(entry.get("yellowServiceDay"), "yellow", "green"),
        _rule_alternating(entry.get("greenServiceDay"), "green", "yellow"),
    ]


@_tab(INDEPENDENT_YELLOW_ZONE)
def _independent_yellow_zone(entry: dict) -> list[tuple | None]:
    return [
        _rule_weekly(entry.get("redServiceDay"), "red"),
        _rule_weekly(entry.get("redServiceDay2"), "red"),
        _rule_weekly(entry.get("yellowServiceDay"), "yellow"),
        _rule_even_only(entry.get("greenServiceDay"), "green"),
        _rule_odd_only(entry.get("greenServiceDay"), "green"),
    ]


@_tab(COMBINED_RED_YELLOW)
def _combined_red_yellow(entry: dict) -> list[tuple | None]:
    return [
        _rule_weekly(entry.get("redServiceDay"), "red"),
        _rule_weekly(entry.get("yellowServiceDay"), "yellow"),
    ]


@_tab(DUAL_COLLECTION_VARIANT)
def _dual_collection_variant(entry: dict) -> list[tuple | None]:
    return [
        _rule_weekly(entry.get("redServiceDay"), "red"),
        _rule_weekly(entry.get("redServiceDay2"), "red"),
        _rule_alternating(entry.get("yellowServiceDay"), "yellow", "green"),
        _rule_weekly(entry.get("greenServiceDay"), "green"),
    ]


@_tab(MULTI_UNIT_BUILDING)
def _multi_unit_building(entry: dict) -> list[tuple | None]:
    return [
        _rule_weekly(entry.get("redServiceDay"), "red"),
        _rule_weekly(entry.get("redServiceDay2"), "red"),
        _rule_weekly(entry.get("redServiceDay3"), "red"),
        _rule_weekly(entry.get("yellowServiceDay"), "yellow"),
        _rule_weekly(entry.get("greenServiceDay"), "green"),
    ]


@_tab(LARGE_COMPLEX)
def _large_complex(entry: dict) -> list[tuple | None]:
    return [
        _rule_weekly(entry.get("redServiceDay"), "red"),
        _rule_weekly(entry.get("redServiceDay2"), "red"),
        _rule_weekly(entry.get("redServiceDay3"), "red"),
        _rule_weekly(entry.get("redServiceDay4"), "red"),
        _rule_weekly(entry.get("yellowServiceDay"), "yellow"),
        _rule_weekly(entry.get("greenServiceDay"), "green"),
    ]


@_rule
def _weekly(pattern: dict, day: str, color: str, is_zone_a: bool) -> None:
    pattern["even_week"].append((day, color))
    pattern["odd_week"].append((day, color))


@_rule
def _alternating(
    pattern: dict, day: str, zone_a_even: str, zone_a_odd: str, is_zone_a: bool
) -> None:
    if is_zone_a:
        pattern["even_week"].append((day, zone_a_even))
        pattern["odd_week"].append((day, zone_a_odd))
    else:
        pattern["even_week"].append((day, zone_a_odd))
        pattern["odd_week"].append((day, zone_a_even))


@_rule
def _even_only(pattern: dict, day: str, color: str, is_zone_a: bool) -> None:
    if is_zone_a:
        pattern["even_week"].append((day, color))


@_rule
def _odd_only(pattern: dict, day: str, color: str, is_zone_a: bool) -> None:
    if not is_zone_a:
        pattern["odd_week"].append((day, color))


def _build_pattern(
    is_zone_a: bool, rules: list[tuple | None]
) -> dict[str, list[tuple]]:
    pattern: dict[str, list[tuple]] = {"even_week": [], "odd_week": []}
    for rule in rules:
        if not rule:
            continue
        rule_type, day, *args = rule
        handler = _RULE_REGISTRY.get(rule_type)
        if handler and day:
            handler(pattern, day, *args, is_zone_a)
    return pattern


def _get_base_pattern(entry: dict) -> dict[str, list[tuple]]:
    tab = entry.get("tab") or ""
    zone = entry.get("zone") or ""
    is_zone_a = zone == ZONE_A
    rule_factory = _TAB_REGISTRY.get(tab)
    if not rule_factory:
        return {"even_week": [], "odd_week": []}
    rules = rule_factory(entry)
    return _build_pattern(is_zone_a, rules)


def find_entry(data: list[dict], address: str) -> dict:
    for row in data:
        if row.get("fullAddress", "").lower() == address.strip().lower():
            return row
    normalised = [(row, _normalise(row.get("fullAddress", ""))) for row in data]
    exact = [row for row, full in normalised if full == _normalise(address)]
    if len(exact) == 1:
        return exact[0]
    if exact:
        raise SourceArgumentNotFoundWithSuggestions(
            "address",
            address.strip().lower(),
            [row["fullAddress"] for row in exact[:10]],
        )
    partial = [row for row, full in normalised if _normalise(address) in full]
    if len(partial) == 1:
        return partial[0]
    if partial:
        suggestions = [row["fullAddress"] for row in partial[:10]]
        raise SourceArgumentNotFoundWithSuggestions(
            "address", address.strip().lower(), suggestions
        )
    raise SourceArgumentNotFound("address", address.strip().lower())


def assets(source, response):
    soup = BeautifulSoup(response.text, "html.parser")
    scripts = [
        urljoin(response.url, str(s["src"]))
        for s in soup.select("script[src]")
        if re.search(r"/main\.[^/]+\.js$", str(s["src"]))
    ]
    if len(scripts) != 1:
        raise ValueError("Cannot identify the Canterbury-Bankstown application bundle")
    return (urljoin(response.url, "streetData.json.gz"), scripts[0])


class CalendarParser(Parser[list[Schedule]]):
    def __call__(self, responses, source=None):
        if source is None:
            raise ValueError("Address matching requires a source")
        data_response, script = responses
        data = json.loads(gzip.decompress(data_response.content))
        entry = find_entry(data, source.params["address"])
        match = re.search(
            r"new Date\(\s*(20\d{2})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*\)", script.text
        )
        if not match:
            raise ValueError("Published bin-week anchor is missing")
        anchor = datetime.date(int(match[1]), int(match[2]) + 1, int(match[3]))
        even = recurrence.next_weekday(0, on_or_after=anchor)
        pattern = _get_base_pattern(entry)
        if not any(pattern.values()):
            raise ValueError(f"Unsupported published bin model: {entry.get('tab')!r}")
        today = datetime.date.today()
        result = []
        for offset, name in ((0, "even_week"), (7, "odd_week")):
            for day, colour in pattern[name]:
                weekday = recurrence.weekday(day)
                if weekday is None:
                    raise ValueError(f"Unrecognized published weekday: {day}")
                result.append(
                    Schedule(
                        colour,
                        even + datetime.timedelta(days=offset + weekday),
                        step=recurrence.FORTNIGHTLY,
                        not_before=today,
                        until=datetime.date(today.year, 12, 31),
                    )
                )
        return result
