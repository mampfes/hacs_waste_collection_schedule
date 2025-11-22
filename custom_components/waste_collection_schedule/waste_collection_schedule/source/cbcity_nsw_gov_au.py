import calendar
import datetime
import gzip
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Canterbury-Bankstown (NSW)"
DESCRIPTION = "City of Canterbury-Bankstown bin day finder"
URL = "https://bindayfinder.azurewebsites.net"
DATA_URL = f"{URL}/streetData.json.gz"
BIN_ICON = "mdi:delete-circle-outline"
BIN_COLORS = {
    "red": "🔴",
    "yellow": "🟡",
    "green": "🟢",
}

ICON_MAP = {
    f"{emoji} {color.title()} Bin": BIN_ICON
    for color, emoji in BIN_COLORS.items()
}

CACHE_DURATION = 30 * 24 * 60 * 60  # 30 days

TEST_CASES = {
    "Tab 1 Zone A": {
        "address": "102 Crinan Street, Hurlstone Park 2193",
    },
    "Tab 1 Zone B": {
        "address": "1 / 1 Aster Avenue, Punchbowl 2196",
    },
    "Tab 2a": {
        "address": "1 / 1 Bellevue Avenue, Lakemba 2195",
    },
    "Tab 2b": {
        "address": "1 / 1 Carysfield Road, Bass Hill 2197",
    },
    "Tab 2c": {
        "address": "1 / 1 Carmen Street, Bankstown 2200",
    },
    "Tab 3": {
        "address": "1 / 1 Fabos Place, Croydon Park 2133",
    },
    "Tab 4": {
        "address": "1 / 1 Charles Street, Canterbury 2193",
    },
    "Tab 5": {
        "address": "1 / 7 Cross Street, Bankstown 2200",
    },
    "Tab 6": {
        "address": "32 Kitchener Parade, Bankstown 2200",
    },
}

WEEKDAY_MAP = {name: i for i, name in enumerate(calendar.day_name)}

ANCHOR_DATE = datetime.date(2021, 3, 7)

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


def _date_for_weekday(name: str | None) -> datetime.date | None:
    if not name or name not in WEEKDAY_MAP:
        return None
    today = datetime.date.today()
    target_weekday = WEEKDAY_MAP[name]
    current_weekday = today.weekday()
    days_ahead = (target_weekday - current_weekday) % 7
    if days_ahead == 0:
        return today
    return today + datetime.timedelta(days=days_ahead)


_TAB_REGISTRY = {}
_RULE_REGISTRY = {}


def _tab(tab_id: str):
    def decorator(func):
        _TAB_REGISTRY[tab_id] = func
        return func
    return decorator


def _rule(func):
    rule_type = func.__name__.removeprefix('_')
    _RULE_REGISTRY[rule_type] = func
    return func


def _rule_weekly(day: str | None, color: str) -> tuple | None:
    return ('weekly', day, color) if day else None


def _rule_alternating(day: str | None, zone_a_even: str, zone_a_odd: str) -> tuple | None:
    return ('alternating', day, zone_a_even, zone_a_odd) if day else None


def _rule_even_only(day: str | None, color: str) -> tuple | None:
    return ('even_only', day, color) if day else None


def _rule_odd_only(day: str | None, color: str) -> tuple | None:
    return ('odd_only', day, color) if day else None


@_tab(STANDARD_RESIDENTIAL)
def _standard_residential(entry: dict) -> list[tuple]:
    return [
        _rule_weekly(entry.get("redServiceDay"), 'red'),
        _rule_alternating(entry.get("yellowServiceDay"), 'yellow', 'green'),
    ]


@_tab(DUAL_COLLECTION)
def _dual_collection(entry: dict) -> list[tuple]:
    return [
        _rule_weekly(entry.get("redServiceDay"), 'red'),
        _rule_weekly(entry.get("yellowServiceDay"), 'yellow'),
        _rule_weekly(entry.get("greenServiceDay"), 'green'),
    ]


@_tab(DUAL_COLLECTION_ALT)
def _dual_collection_alt(entry: dict) -> list[tuple]:
    return [
        _rule_weekly(entry.get("redServiceDay"), 'red'),
        _rule_weekly(entry.get("redServiceDay2"), 'red'),
        _rule_alternating(entry.get("yellowServiceDay"), 'yellow', 'green'),
        _rule_alternating(entry.get("greenServiceDay"), 'green', 'yellow'),
    ]


@_tab(INDEPENDENT_YELLOW_ZONE)
def _independent_yellow_zone(entry: dict) -> list[tuple]:
    return [
        _rule_weekly(entry.get("redServiceDay"), 'red'),
        _rule_weekly(entry.get("redServiceDay2"), 'red'),
        _rule_weekly(entry.get("yellowServiceDay"), 'yellow'),
        _rule_even_only(entry.get("greenServiceDay"), 'green'),
        _rule_odd_only(entry.get("greenServiceDay"), 'green'),
    ]


@_tab(COMBINED_RED_YELLOW)
def _combined_red_yellow(entry: dict) -> list[tuple]:
    return [
        _rule_weekly(entry.get("redServiceDay"), 'red'),
        _rule_weekly(entry.get("yellowServiceDay"), 'yellow'),
    ]


@_tab(DUAL_COLLECTION_VARIANT)
def _dual_collection_variant(entry: dict) -> list[tuple]:
    return [
        _rule_weekly(entry.get("redServiceDay"), 'red'),
        _rule_weekly(entry.get("redServiceDay2"), 'red'),
        _rule_alternating(entry.get("yellowServiceDay"), 'yellow', 'green'),
        _rule_weekly(entry.get("greenServiceDay"), 'green'),
    ]


@_tab(MULTI_UNIT_BUILDING)
def _multi_unit_building(entry: dict) -> list[tuple]:
    return [
        _rule_weekly(entry.get("redServiceDay"), 'red'),
        _rule_weekly(entry.get("redServiceDay2"), 'red'),
        _rule_weekly(entry.get("redServiceDay3"), 'red'),
        _rule_weekly(entry.get("yellowServiceDay"), 'yellow'),
        _rule_weekly(entry.get("greenServiceDay"), 'green'),
    ]


@_tab(LARGE_COMPLEX)
def _large_complex(entry: dict) -> list[tuple]:
    return [
        _rule_weekly(entry.get("redServiceDay"), 'red'),
        _rule_weekly(entry.get("redServiceDay2"), 'red'),
        _rule_weekly(entry.get("redServiceDay3"), 'red'),
        _rule_weekly(entry.get("redServiceDay4"), 'red'),
        _rule_weekly(entry.get("yellowServiceDay"), 'yellow'),
        _rule_weekly(entry.get("greenServiceDay"), 'green'),
    ]


@_rule
def _weekly(pattern: dict, day: str, color: str, is_zone_a: bool) -> None:
    pattern['even_week'].append((day, color))
    pattern['odd_week'].append((day, color))


@_rule
def _alternating(pattern: dict, day: str, zone_a_even: str, zone_a_odd: str, is_zone_a: bool) -> None:
    if is_zone_a:
        pattern['even_week'].append((day, zone_a_even))
        pattern['odd_week'].append((day, zone_a_odd))
    else:
        pattern['even_week'].append((day, zone_a_odd))
        pattern['odd_week'].append((day, zone_a_even))


@_rule
def _even_only(pattern: dict, day: str, color: str, is_zone_a: bool) -> None:
    if is_zone_a:
        pattern['even_week'].append((day, color))


@_rule
def _odd_only(pattern: dict, day: str, color: str, is_zone_a: bool) -> None:
    if not is_zone_a:
        pattern['odd_week'].append((day, color))


def _build_pattern(is_zone_a: bool, rules: list[tuple | None]) -> dict[str, list[tuple]]:
    pattern = {'even_week': [], 'odd_week': []}

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
        return {'even_week': [], 'odd_week': []}

    rules = rule_factory(entry)
    return _build_pattern(is_zone_a, rules)


def _repeat_pattern_until_eoy(pattern: dict[str, list[tuple]]) -> list[Collection]:
    today = datetime.date.today()
    end_of_year = datetime.date(today.year, 12, 31)
    collections = []

    current_week_start = today - datetime.timedelta(days=today.weekday())

    while current_week_start <= end_of_year:
        weeks_since_anchor = (current_week_start - ANCHOR_DATE).days // 7
        is_even_week = weeks_since_anchor % 2 == 0
        week_pattern = pattern['even_week'] if is_even_week else pattern['odd_week']

        for weekday_name, bin_color in week_pattern:
            weekday_num = WEEKDAY_MAP.get(weekday_name)
            if weekday_num is None:
                continue

            collection_date = current_week_start + datetime.timedelta(days=weekday_num)

            if today <= collection_date <= end_of_year:
                emoji = BIN_COLORS.get(bin_color, "")
                bin_name = f"{emoji} {bin_color.title()} Bin"
                collections.append(Collection(
                    date=collection_date,
                    t=bin_name,
                    icon=ICON_MAP.get(bin_name)
                ))

        current_week_start += datetime.timedelta(days=7)

    return collections


class Source:
    _cached_data: list[dict] | None = None
    _cache_timestamp: float | None = None
    _cache_etag: str | None = None

    def __init__(self, address: str):
        self._address = address.strip().lower()

    @classmethod
    def _is_cache_valid(cls) -> bool:
        if cls._cached_data is None or cls._cache_timestamp is None:
            return False

        now = datetime.datetime.now()
        cache_time = datetime.datetime.fromtimestamp(cls._cache_timestamp)

        age = now.timestamp() - cls._cache_timestamp
        if age >= CACHE_DURATION:
            return False

        if now.month == 1:
            first_day = datetime.datetime(now.year, 1, 1)
            days_until_sunday = (6 - first_day.weekday()) % 7
            if days_until_sunday == 0:
                first_sunday = first_day
            else:
                first_sunday = first_day + datetime.timedelta(days=days_until_sunday)

            if now >= first_sunday and cache_time < first_sunday:
                return False

        return True

    @classmethod
    def _load_streets(cls) -> list[dict]:
        if cls._is_cache_valid():
            return cls._cached_data  # type: ignore

        headers = {"User-Agent": "Mozilla/5.0"}
        if cls._cache_etag:
            headers["If-None-Match"] = cls._cache_etag

        try:
            response = requests.get(DATA_URL, headers=headers, timeout=30)

            if response.status_code == 304 and cls._cached_data:
                cls._cache_timestamp = datetime.datetime.now().timestamp()
                return cls._cached_data

            response.raise_for_status()

            decompressed = gzip.decompress(response.content)
            data = json.loads(decompressed.decode("utf-8"))

            cls._cached_data = data
            cls._cache_timestamp = datetime.datetime.now().timestamp()
            cls._cache_etag = response.headers.get("ETag")

            return data

        except Exception as e:
            if cls._cached_data:
                return cls._cached_data
            raise ValueError(
                f"Failed to fetch street data from {DATA_URL}: {e}"
            ) from e

    def _find_entry(self, data: list[dict]) -> dict:
        for row in data:
            if row.get("fullAddress", "").lower() == self._address:
                return row
        for row in data:
            if self._address in row.get("fullAddress", "").lower():
                return row
        raise ValueError(f"Address not found in Canterbury-Bankstown dataset: {self._address}")

    def fetch(self) -> list[Collection]:
        dataset = self._load_streets()
        entry = self._find_entry(dataset)
        pattern = _get_base_pattern(entry)
        collections = _repeat_pattern_until_eoy(pattern)
        collections.sort(key=lambda c: c.date)
        return collections
