import json
import re
from datetime import date, timedelta
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import ArcGisZoneParser
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

# Boroondara has no FeatureServer to query: the collection zones ship as a
# GeoJSON bundle embedded in the council's own JS (main-v2.min.js), so the
# shared ArcGisZoneParser geocodes the address and matches it against those
# polygons. The only source-specific part is _zones(), which cuts the GeoJSON
# out of the script and quotes its JS object keys. Once the matched zone (day +
# A/B week) is known, the weekly/fortnightly cadence it describes is projected
# via the shared RecurrenceExpander.

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


def _geocode_address(address: str, **_: Any) -> str:
    """Qualify the address so the world geocoder lands in the right Melbourne."""
    return f"{address}, Victoria, Australia"


def _zones(response, source) -> dict:
    """Cut the zone GeoJSON out of the council's minified JS bundle."""
    data = response.text
    start = data.find("const polygonData=") + len("const polygonData=")
    end_match = re.search(r'week:"[AB]"\}\}\]\}', data)
    if not end_match:
        raise SourceArgumentNotFound(
            "address",
            source.params["address"],
            "could not read the collection zone data.",
        )
    # Convert the JS object literal (unquoted keys) to valid JSON.
    geojson_js = data[start : end_match.end()]
    return json.loads(re.sub(r'(?<!["\w])([a-zA-Z_]\w*):', r'"\1":', geojson_js))


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

    retrieve = retrievers.HttpGetRetriever(url=JS_URL, timeout=30)
    parse = ArcGisZoneParser(extract=_zones, address=_geocode_address)
    preprocess = RecurrenceExpander(_describe)
    transform = RowTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())
