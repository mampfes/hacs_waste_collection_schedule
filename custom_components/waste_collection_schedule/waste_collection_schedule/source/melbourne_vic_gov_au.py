from datetime import date, datetime, timedelta
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import coords
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.transformers import ICSTransformer

API_URL = (
    "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/"
    "garbage-collection-zones/records"
)
SCHEDULE_DAYS = 365

_TYPE_MAP = {
    "General waste": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
}


def _describe(zone: dict, source):
    """One weekly/fortnightly cadence per service (``rub_*`` rubbish, ``rec_*`` recycling)."""
    today = date.today()
    for prefix in ("rub", "rec"):
        weekday = recurrence.weekday(zone.get(f"{prefix}_day") or "")
        if weekday is None:
            continue
        weeks = int(zone.get(f"{prefix}_weeks") or 1)
        try:
            start = datetime.strptime(zone[f"{prefix}_start"], "%Y/%m/%d").date()
        except (KeyError, ValueError, TypeError):
            start = today
        first = start + timedelta(days=(weekday - start.weekday()) % 7)
        yield Schedule(
            zone[f"{prefix}_name"],
            first,
            recurrence.WEEKLY * weeks,
            count=SCHEDULE_DAYS // (7 * weeks) + 1,
            anchor=True,
        )


@final
class Source(BaseSource):
    TITLE = "City of Melbourne"
    DESCRIPTION = "Source for City of Melbourne waste collection schedules."
    URL = "https://www.melbourne.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Monday zone (North Melbourne area)": {
            "lat": -37.78888528182715,
            "lon": 144.94807224053946,
        },
        "Tuesday zone (CBD south)": {
            "lat": -37.82597212079299,
            "lon": 144.946122910589,
        },
        "Wednesday zone (Carlton area)": {
            "lat": -37.797770217788965,
            "lon": 144.96108202950762,
        },
        "Thursday zone (West Melbourne area)": {
            "lat": -37.80199461843715,
            "lon": 144.92363364191561,
        },
        "Friday zone (East Melbourne area)": {
            "lat": -37.81350068415623,
            "lon": 144.98033118663488,
        },
    }

    PARAMS = (coords("lat", "lon"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Pick the location of your property on the map. The collection "
            "zone of the City of Melbourne that contains it is used."
        ),
    }

    retrieve = retrievers.Request(
        API_URL,
        params=lambda lat, lon, **_: {
            "limit": 1,
            "select": "rub_name,rec_name,rub_day,rec_day,rub_weeks,rec_weeks,rub_start,rec_start",
            "where": f"intersects(geo_shape, geom'POINT({float(lon)} {float(lat)})')",
        },
    )

    parse = parsers.JsonParser("results")

    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)
