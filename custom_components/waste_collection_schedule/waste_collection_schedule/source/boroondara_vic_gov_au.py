import json
import re
from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import ArcGisError, geocode
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

# Boroondara has no FeatureServer to query: the ArcGIS World GeocodeServer
# resolves the address to a point (the one thing the shared ArcGis service
# still contributes here), but the collection zone comes from a bespoke
# JS-embedded GeoJSON bundle (main-v2.min.js) matched by point-in-polygon, not
# an ArcGIS /query. That combination -- a hand-rolled JS-object-literal parse
# plus a point-in-polygon match -- is a genuinely irregular flow no configured
# retriever/parser expresses, so retrieve/parse are overridden as methods
# (same shape as jacksonville_fl_us.py). Once the matched zone (day + A/B
# week) is known, the recurring weekly/fortnightly cadence it describes is
# projected via the shared RecurrenceExpander rather than hand-rolled date
# maths.

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

# Waste-type keys emitted by _describe -> canonical WasteType.
RECYCLING = "Recycling"
FOGO = "FOGO"
GENERAL = "General Waste"

_TYPE_MAP = {
    RECYCLING: RECYCLABLES,
    FOGO: ORGANIC,
    GENERAL: GENERAL_WASTE,
}

# Number of collections to project for each stream (matches the legacy default).
WEEKS_AHEAD = 8


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


def _describe(zone: dict, source):
    weekday = _WEEKDAYS[zone["day"]]
    weekly_start = recurrence.next_weekday(weekday)
    yield Schedule(RECYCLING, weekly_start, recurrence.WEEKLY, WEEKS_AHEAD)
    yield Schedule(FOGO, weekly_start, recurrence.WEEKLY, WEEKS_AHEAD)

    fortnight_start = weekly_start
    if _get_week_type(fortnight_start) != zone["week"]:
        fortnight_start += timedelta(weeks=1)
    yield Schedule(GENERAL, fortnight_start, recurrence.FORTNIGHTLY, WEEKS_AHEAD)


@final
class Source(BaseSource):
    TITLE = "City of Boroondara"
    DESCRIPTION = "Source for City of Boroondara waste collection."
    URL = "https://www.boroondara.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "211 Mont Albert Road Surrey Hills": {
            "address": "211 Mont Albert Road, Surrey Hills"
        },
        "60 Barkers Road Hawthorn East": {"address": "60 Barkers Road, Hawthorn East"},
        "1 Kew Boulevard Kew": {"address": "1 Kew Boulevard, Kew"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Street address within Boroondara (e.g. '211 Mont Albert Road, Surrey Hills').",
    }

    preprocess = RecurrenceExpander(_describe)
    transform = RowTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())

    def retrieve(self, source: "Source"):
        return self.session.get(JS_URL, timeout=30)

    def parse(self, response, source: "Source | None" = None) -> list[dict]:
        address = self.params["address"]
        try:
            location = geocode(f"{address}, Victoria, Australia")
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", address) from e

        data = response.text
        start = data.find("const polygonData=") + len("const polygonData=")
        end_match = re.search(r'week:"[AB]"\}\}\]\}', data)
        if not end_match:
            raise SourceArgumentNotFound(
                "address", address, "could not read the collection zone data."
            )
        geojson_js = data[start : end_match.end()]

        # Convert JS object literal (unquoted keys) to valid JSON
        geojson_str = re.sub(r'(?<!["\w])([a-zA-Z_]\w*):', r'"\1":', geojson_js)
        features = json.loads(geojson_str)["features"]

        lat, lng = location["y"], location["x"]
        for feature in features:
            coords = feature["geometry"]["coordinates"][0]
            if _point_in_polygon(lng, lat, coords):
                return [feature["properties"]]

        raise SourceArgumentNotFound("address", address)
