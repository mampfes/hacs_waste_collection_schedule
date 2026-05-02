import json
import logging
import re
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import ArcGisError, geocode

TITLE = "City of Boroondara"
DESCRIPTION = "Source for City of Boroondara waste collection."
URL = "https://www.boroondara.vic.gov.au"
TEST_CASES = {
    "211 Mont Albert Road Surrey Hills": {
        "address": "211 Mont Albert Road, Surrey Hills"
    },
    "60 Barkers Road Hawthorn East": {"address": "60 Barkers Road, Hawthorn East"},
    "1 Kew Boulevard Kew": {"address": "1 Kew Boulevard, Kew"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "FOGO": "mdi:leaf",
    "Recycling": "mdi:recycle",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address within Boroondara (e.g. '211 Mont Albert Road, Surrey Hills')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

_LOGGER = logging.getLogger(__name__)

JS_URL = "https://cdn.boroondara.vic.gov.au/binday/js/main-v2.min.js"

# April 2, 2023 (Sunday) — reference date used by Boroondara's JS widget
# to determine A/B recycling week parity.
_REFERENCE_SUNDAY = date(2023, 4, 2)

_WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
}


def _fetch_zones() -> list:
    r = requests.get(JS_URL, timeout=30)
    r.raise_for_status()
    data = r.text

    start = data.find("const polygonData=") + len("const polygonData=")
    end_match = re.search(r'week:"[AB]"\}\}\]\}', data)
    if not end_match:
        raise ValueError("Could not locate polygon data in Boroondara JS")
    geojson_js = data[start : end_match.end()]

    # Convert JS object literal (unquoted keys) to valid JSON
    geojson_str = re.sub(r'(?<!["\w])([a-zA-Z_]\w*):', r'"\1":', geojson_js)
    return json.loads(geojson_str)["features"]


def _point_in_polygon(x: float, y: float, polygon: list) -> bool:
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if min(p1y, p2y) < y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y:
                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            if p1x == p2x or x <= xinters:
                inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def _get_week_type(d: date) -> str:
    """Return 'A' or 'B' for the given date, matching Boroondara's JS parity."""
    days_since_sunday = (d.weekday() + 1) % 7
    sunday = d - timedelta(days=days_since_sunday)
    weeks = (sunday - _REFERENCE_SUNDAY).days // 7
    return "A" if weeks % 2 == 0 else "B"


def _next_weekly(day_name: str, weeks_ahead: int = 8) -> list[date]:
    target = _WEEKDAYS[day_name]
    today = date.today()
    days_ahead = (target - today.weekday()) % 7 or 7
    first = today + timedelta(days=days_ahead)
    return [first + timedelta(weeks=i) for i in range(weeks_ahead)]


def _next_fortnightly(
    day_name: str, zone_week: str, weeks_ahead: int = 8
) -> list[date]:
    target = _WEEKDAYS[day_name]
    today = date.today()
    days_ahead = (target - today.weekday()) % 7 or 7
    candidate = today + timedelta(days=days_ahead)
    if _get_week_type(candidate) != zone_week:
        candidate += timedelta(weeks=1)
    return [candidate + timedelta(weeks=2 * i) for i in range(weeks_ahead)]


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            loc = geocode(f"{self._address}, Victoria, Australia")
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        lat, lng = loc["y"], loc["x"]

        features = _fetch_zones()
        zone = None
        for feature in features:
            coords = feature["geometry"]["coordinates"][0]
            if _point_in_polygon(lng, lat, coords):
                zone = feature["properties"]
                break

        if zone is None:
            raise SourceArgumentNotFound("address", self._address)

        _LOGGER.debug("Address %s → zone %s", self._address, zone)

        day = zone["day"]
        week = zone["week"]

        entries: list[Collection] = []

        for d in _next_weekly(day):
            entries.append(Collection(d, "General Waste", ICON_MAP["General Waste"]))
            entries.append(Collection(d, "FOGO", ICON_MAP["FOGO"]))

        for d in _next_fortnightly(day, week):
            entries.append(Collection(d, "Recycling", ICON_MAP["Recycling"]))

        return entries
