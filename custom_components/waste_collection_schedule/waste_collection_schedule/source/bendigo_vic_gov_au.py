import datetime
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import coords
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.Pozi import (
    PoziGeoJsonParser,
    PoziGeoJsonRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

# Demonstrates: a Pozi GeoJSON zone lookup by direct lat/lon (no address
# geocoding needed). The zone's properties carry a weekday plus a per-type
# frequency and "next pickup" date; _describe() is the only source-specific
# code, turning those into Schedule descriptors for RecurrenceExpander. Labels
# ("General Waste", "Recycling", "Green Waste") all resolve against the shared
# multilingual vocabulary, so no type_value_map is needed.

ZONES_URL = "https://connect.pozi.com/userdata/bendigo-publisher/Pozi_Public_City_of_Greater_Bendigo/Waste_Collection_Zones.json"

_FREQUENCY_STEP = {"Weekly": recurrence.WEEKLY, "Fortnightly": recurrence.FORTNIGHTLY}

# (frequency field, next-pickup-date field, waste-type label) per collection.
_COLLECTIONS = (
    ("General Waste Frequency", "Next General Waste Pickup", "General Waste"),
    ("Recycling Frequency", "Next Recycling Pickup", "Recycling"),
    ("Organics Frequency", "Next Organics Pickup", "Green Waste"),
)

# How far ahead to project collections (matches the source's original window).
_WINDOW_DAYS = 365


def _describe(zone, source):
    """Yield a Schedule per collection type the zone's properties describe.

    Bendigo publishes a weekday, a per-type frequency and that type's next
    pickup date. If the given "next pickup" date doesn't fall on the stated
    weekday, roll it forward to the next date that does.
    """
    day_name = zone.get("Collection Day")
    weekday = recurrence.weekday(day_name) if day_name else None

    for freq_field, date_field, label in _COLLECTIONS:
        step = _FREQUENCY_STEP.get(zone.get(freq_field))
        start_raw = zone.get(date_field)
        if step is None or not start_raw:
            continue
        try:
            start = datetime.datetime.strptime(start_raw.strip(), "%d-%b-%Y").date()
        except ValueError:
            continue

        if weekday is not None and start.weekday() != weekday:
            days_ahead = (weekday - start.weekday()) % 7 or 7
            start += datetime.timedelta(days=days_ahead)

        end = datetime.date.today() + datetime.timedelta(days=_WINDOW_DAYS)
        if start > end:
            continue
        count = (end - start) // step + 1
        yield Schedule(label, start, step, count)


@final
class Source(BaseSource):
    TITLE = "City of Greater Bendigo"
    DESCRIPTION = "Source for City of Greater Bendigo rubbish collection."
    URL = "https://www.bendigo.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Bunnings Epsom": {
            "latitude": -36.701755710607394,
            "longitude": 144.31310883736967,
        },
        "Bunnings Bendigo": {
            "latitude": -36.808262837180514,
            "longitude": 144.24269331664098,
        },
        "Alfa Kitchen Bendigo": {
            "latitude": -36.758540554036315,
            "longitude": 144.2818129235716,
        },
    }

    PARAMS = (coords(lat="latitude", lon="longitude"),)

    retrieve = PoziGeoJsonRetriever(ZONES_URL, lat="latitude", lon="longitude")
    parse = PoziGeoJsonParser()
    preprocess = RecurrenceExpander(_describe)
    transform = RowTransformer()

    def __init__(self, latitude: float, longitude: float):
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (TypeError, ValueError) as e:
            raise SourceArgumentException(
                "latitude", f"invalid coordinate format: {e}"
            ) from e
        super().__init__(latitude=lat, longitude=lon)
