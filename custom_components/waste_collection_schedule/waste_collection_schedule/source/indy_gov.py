"""Source for City of Indianapolis (Indy DPW / Marion County Solid Waste), USA."""

import logging
import re
from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Indianapolis (Indy DPW / Marion County Solid Waste)"
DESCRIPTION = "Source for City of Indianapolis (Marion County, IN) trash, heavy trash and recycling pickup days."
URL = "https://www.indy.gov"
COUNTRY = "us"
SOURCE_CODEOWNERS = ["@Cornflake5414"]

TEST_CASES = {
    "City-County Building": {"address": "200 E Washington St"},
    "Central Library": {"address": "40 E St Clair St", "recycling_date": "2026-12-03"},
    "Fountain Square Branch Library": {"address": "1066 Virginia Ave"},
    "Decatur Branch Library (LRS district)": {"address": "5301 Kentucky Ave"},
    "Southport Branch Library (lat/lon)": {"lat": 39.650895, "lon": -86.1175485},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your Indianapolis street address (house number and street, e.g. "
        "'200 E Washington St'), or set lat and lon instead. You can check your "
        "trash district at https://www.indy.gov/workflow/trash-pickup. Recycling in "
        "Indianapolis is a biweekly paid subscription; to show it, set recycling_date "
        "to any one known recycling pickup date (YYYY-MM-DD), see "
        "https://www.indy.gov/workflow/recycling."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
        "lat": "Latitude",
        "lon": "Longitude",
        "recycling_date": "Known Recycling Date",
        "include_heavy_trash": "Include Heavy Trash",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Indianapolis street address, e.g. '200 E Washington St' (leave empty if using lat/lon)",
        "lat": "Latitude (WGS84) of the address; use together with lon instead of address",
        "lon": "Longitude (WGS84) of the address; use together with lat instead of address",
        "recycling_date": "Any one known recycling pickup date (YYYY-MM-DD); needed to show the biweekly recycling schedule",
        "include_heavy_trash": "Show monthly heavy trash pickups (only for districts with a fixed day each month)",
    },
}

ICON_MAP = {
    "Trash": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Heavy Trash": Icons.BULKY,
}

GEOCODE_URL = "https://gis.indy.gov/server/rest/services/Locators/IndyAddresses/GeocodeServer/findAddressCandidates"
LAYER_URL = "https://gis.indy.gov/server/rest/services/MyNeighborhood/MyNeighborhoodDynamic/MapServer/18/query"
OUT_FIELDS = "DISTRICT,HAULER,ROUTE_NO,DAY,HVYTRASHDA,RC_HAULER,RC_DAY"
STATE_PLANE_WKID = 2965  # NAD83 / Indiana East (ftUS)
MIN_SCORE = 90
TIMEOUT = 30
WEEKS_AHEAD = 10

SERVED_HAULERS = {"DEPARTMENT OF PUBLIC WORKS", "LRS", "LRS-CONDO CONTRACT"}

WEEKDAYS = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}

DAY_TOKENS = {
    **WEEKDAYS,
    "MON": 0,
    "TUE": 1,
    "TUES": 1,
    "WED": 2,
    "WEDS": 2,
    "THU": 3,
    "THUR": 3,
    "THURS": 3,
    "FRI": 4,
    "SAT": 5,
    "SUN": 6,
    "M": 0,
    "TU": 1,
    "W": 2,
    "TH": 3,
    "R": 3,
    "F": 4,
    "SA": 5,
    "SU": 6,
}
_COMPACT_DAY_RE = re.compile(r"SU|SA|TU|TH|M|W|F")
_COMPACT_FULL_RE = re.compile(r"(?:SU|SA|TU|TH|M|W|F)+")

ORDINALS = {"FIRST": 1, "SECOND": 2, "THIRD": 3, "FOURTH": 4, "FIFTH": 5}
_HEAVY_RE = re.compile(
    r"^\s*(FIRST|SECOND|THIRD|FOURTH|FIFTH)\s+"
    r"(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\s+OF\s+THE\s+MONTH\s*$"
)
_RECYCLING_RE = re.compile(
    r"^\s*EVERY\s+OTHER\s+"
    r"(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\s*$"
)


def _parse_days(value: str | None) -> list[int]:
    """Parse DAY values like 'THURSDAY', 'MON,THU', 'M,Tu,Th,F' or 'MTuWThFSa'."""
    days: list[int] = []
    for raw in re.split(r"[,/&;\s]+", str(value or "").strip().upper()):
        token = raw.strip(". ")
        if not token:
            continue
        if token in DAY_TOKENS:
            found = [DAY_TOKENS[token]]
        elif _COMPACT_FULL_RE.fullmatch(token):
            found = [DAY_TOKENS[t] for t in _COMPACT_DAY_RE.findall(token)]
        else:
            _LOGGER.debug("Ignoring unknown day token '%s' in '%s'", token, value)
            continue
        for wd in found:
            if wd not in days:
                days.append(wd)
    return days


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date | None:
    """Nth weekday of a month, or None if the month has no such day (e.g. 5th)."""
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    d += timedelta(weeks=n - 1)
    return d if d.month == month else None


def _last_weekday(year: int, month: int, weekday: int) -> date:
    d = date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _holidays(year: int) -> list[date]:
    """Holidays on the Indy 'Holidays & Slide Schedules' list (actual dates)."""
    days = [
        date(year, 1, 1),  # New Year's Day
        _nth_weekday(year, 1, 0, 3),  # Martin Luther King Jr. Day
        _last_weekday(year, 5, 0),  # Memorial Day
        date(year, 6, 19),  # Juneteenth
        date(year, 7, 4),  # Independence Day
        _nth_weekday(year, 9, 0, 1),  # Labor Day
        _nth_weekday(year, 11, 3, 4),  # Thanksgiving
        date(year, 12, 25),  # Christmas
    ]
    return [d for d in days if d is not None]


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _shift_for_holiday(d: date, holidays: set[date]) -> date:
    """Slide a pickup one day if a weekday holiday falls on/before it in the same week."""
    monday = _week_start(d)
    for h in holidays:
        if h.weekday() < 5 and _week_start(h) == monday and d >= h:
            return d + timedelta(days=1)
    return d


def _parse_date(param: str, value) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError as e:
        raise SourceArgumentException(
            param, f"Invalid {param} '{value}', expected format YYYY-MM-DD."
        ) from e


def _parse_coord(param: str, value, limit: float) -> float | None:
    if value in (None, ""):
        return None
    try:
        f = float(value)
    except (TypeError, ValueError) as e:
        raise SourceArgumentException(
            param, f"Invalid {param} '{value}', expected a decimal number."
        ) from e
    if not -limit <= f <= limit:
        raise SourceArgumentException(param, f"{param} '{value}' is out of range.")
    return f


def _get_json(url: str, params: dict) -> dict:
    r = requests.get(url, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and data.get("error"):
        err = data["error"]
        msg = err.get("message") if isinstance(err, dict) else err
        raise requests.exceptions.RequestException(
            f"Indianapolis GIS service returned an error: {msg}"
        )
    return data


class Source:
    def __init__(
        self,
        address: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        recycling_date: str | date | None = None,
        include_heavy_trash: bool = True,
    ):
        self._address = re.sub(r"\s+", " ", str(address or "")).strip()
        self._lat = _parse_coord("lat", lat, 90)
        self._lon = _parse_coord("lon", lon, 180)
        if not self._address:
            if self._lat is None or self._lon is None:
                raise SourceArgumentExceptionMultiple(
                    ["address", "lat", "lon"],
                    "Provide either an address or both lat and lon.",
                )
        self._recycling_date = _parse_date("recycling_date", recycling_date)
        self._include_heavy_trash = bool(include_heavy_trash)

    def _geocode(self) -> tuple[float, float]:
        data = _get_json(
            GEOCODE_URL,
            {
                "SingleLine": self._address,
                "f": "json",
                "maxLocations": 3,
                "outSR": STATE_PLANE_WKID,
            },
        )
        candidates = data.get("candidates") or []
        if candidates and float(candidates[0].get("score") or 0) >= MIN_SCORE:
            loc = candidates[0]["location"]
            return float(loc["x"]), float(loc["y"])
        suggestions = [c["address"] for c in candidates if c.get("address")]
        if suggestions:
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, suggestions
            )
        raise SourceArgumentNotFound(
            "address",
            self._address,
            "the Indianapolis address locator could not find it. Use house number "
            "and street, e.g. '200 E Washington St'.",
        )

    def _get_district(self) -> dict:
        if self._address:
            x, y = self._geocode()
            in_sr = STATE_PLANE_WKID
        else:
            x, y = self._lon, self._lat  # type: ignore[assignment]
            in_sr = 4326
        data = _get_json(
            LAYER_URL,
            {
                "geometry": f"{x},{y}",
                "geometryType": "esriGeometryPoint",
                "inSR": in_sr,
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": OUT_FIELDS,
                "returnGeometry": "false",
                "f": "json",
            },
        )
        features = data.get("features") or []
        if not features:
            arg = "address" if self._address else "lat"
            value = self._address or f"{self._lat},{self._lon}"
            raise SourceArgumentNotFound(
                arg,
                value,
                "this location is not inside an Indianapolis trash district.",
            )
        return features[0].get("attributes") or {}

    def fetch(self) -> list[Collection]:
        attrs = self._get_district()
        arg = "address" if self._address else "lat"

        hauler = str(attrs.get("HAULER") or "").strip().upper()
        day_raw = str(attrs.get("DAY") or "").strip().upper()
        if hauler not in SERVED_HAULERS or day_raw in ("", "EXCL", "EXCLUDED"):
            raise SourceArgumentException(
                arg,
                f"This address is not served by the City of Indianapolis "
                f"({hauler.title() or 'unknown hauler'}); contact your town/hauler.",
            )

        trash_days = _parse_days(day_raw)
        if not trash_days:
            raise SourceArgumentException(
                arg, f"Could not understand the trash pickup day '{day_raw}'."
            )

        start = _week_start(date.today())
        end = start + timedelta(weeks=WEEKS_AHEAD)
        holidays = {h for y in range(start.year, end.year + 1) for h in _holidays(y)}

        seen: set[tuple[date, str]] = set()
        entries: list[Collection] = []

        def add(nominal: date, name: str) -> None:
            d = _shift_for_holiday(nominal, holidays)
            if not start <= d <= end or (d, name) in seen:
                return
            seen.add((d, name))
            entries.append(Collection(date=d, t=name, icon=ICON_MAP.get(name)))

        # Weekly trash
        week = start
        while week < end:
            for wd in trash_days:
                add(week + timedelta(days=wd), "Trash")
            week += timedelta(weeks=1)

        # Heavy trash: Nth weekday of the month
        if self._include_heavy_trash:
            heavy_raw = str(attrs.get("HVYTRASHDA") or "").strip().upper()
            m = _HEAVY_RE.match(heavy_raw)
            if m:
                n, wd = ORDINALS[m.group(1)], WEEKDAYS[m.group(2)]
                y, mo = start.year, start.month
                while date(y, mo, 1) < end:
                    d = _nth_weekday(y, mo, wd, n)
                    if d is not None and start <= d < end:
                        add(d, "Heavy Trash")
                    y, mo = (y + 1, 1) if mo == 12 else (y, mo + 1)
            else:
                _LOGGER.debug(
                    "Heavy trash rule '%s' has no fixed day; not shown", heavy_raw
                )

        # Biweekly recycling (paid subscription)
        rc_raw = str(attrs.get("RC_DAY") or "").strip().upper()
        m = _RECYCLING_RE.match(rc_raw)
        if m and self._recycling_date is not None:
            wd = WEEKDAYS[m.group(1)]
            ref_week = _week_start(self._recycling_date)
            week = start
            while week < end:
                if ((week - ref_week).days // 7) % 2 == 0:
                    add(week + timedelta(days=wd), "Recycling")
                week += timedelta(weeks=1)
        elif m:
            _LOGGER.debug(
                "Recycling day is '%s' but no recycling_date is set; recycling "
                "(paid subscription) not shown",
                rc_raw,
            )
        else:
            _LOGGER.debug("Recycling day '%s' not recognised; not shown", rc_raw)

        entries.sort(key=lambda c: (c.date, c.type))
        return entries
