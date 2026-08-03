from datetime import date, datetime, timedelta
from typing import Any, ClassVar, final

from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service import ArcGis, NewEdgeServices
from waste_collection_schedule.transformers import ICSTransformer

# CWD (North Texas) publishes pickup days/frequency per service across SIX ArcGIS
# FeatureServer layers, queried with a single spatial point each. The geocode
# also asks for the City field, because the holiday overlay is published per
# community on the hauler's New Edge Services support portal rather than on the
# route layers.
#
# The pipeline is therefore: ArcGisMultiFeatureRetriever (one geocode with
# geocode_fields="City", then one spatial query per layer) -> the multi-layer
# parser keeping each layer's single matching route -> _describe projecting the
# route's cadence into count=1 Schedules -> the New Edge holiday overlay
# sliding whichever of those land on a holiday.

FEATURE_BASE = "https://services3.arcgis.com/xeSJphIgrY4QfLVq/arcgis/rest/services/CWD_Routes_View/FeatureServer"

# Layer id -> legacy raw ``t=`` string (the key into _TYPE_MAP below).
LAYER_TYPES = {
    0: "HHW",
    1: "Recycling",
    2: "Trash",
    3: "Bulk Waste",
    4: "Yard Waste",
    5: "Compost",
}

LAYERS = [
    (raw_type, f"{FEATURE_BASE}/{layer_id}")
    for layer_id, raw_type in LAYER_TYPES.items()
]

_TYPE_MAP = {
    "HHW": wt.HAZARDOUS,
    "Recycling": wt.RECYCLABLES,
    "Trash": wt.GENERAL_WASTE,
    "Bulk Waste": wt.BULKY_WASTE,
    "Yard Waste": wt.GARDEN_WASTE,
    "Compost": wt.ORGANIC,
}

WEEKDAY_MAP = {
    "Monday": MO,
    "Tuesday": TU,
    "Wednesday": WE,
    "Thursday": TH,
    "Friday": FR,
    "Saturday": SA,
    "Sunday": SU,
}


def _community(source: Any) -> str:
    """The city the geocoder matched, which keys the portal's holiday table."""
    return ArcGis.geocoded_location(source).get("attributes", {}).get("City", "")


def _generate_dates(
    day_name: str,
    frequency: str,
    timing_week: str,
    start_date: date,
    end_date: date,
) -> list[date]:
    """Project a recurring pickup day into concrete dates."""
    weekday = WEEKDAY_MAP.get(day_name)
    if not weekday:
        return []

    rule = rrule(
        WEEKLY,
        byweekday=weekday,
        dtstart=datetime.combine(start_date, datetime.min.time()),
        until=datetime.combine(end_date, datetime.min.time()),
    )
    all_dates = [d.date() for d in rule]

    if "1st" in timing_week:
        return [d for d in all_dates if d.day <= 7]
    if "biweekly" in frequency:
        return [d for d in all_dates if d.isocalendar()[1] % 2 == 1]
    return all_dates


def _describe(record, source):
    """Yield one ``count=1`` Schedule per concrete pickup date for a layer."""
    raw_type, attrs = record

    pickup_days = [
        d.strip()
        for key in ("PickupDay1", "PickupDay2")
        if (d := attrs.get(key))
        and isinstance(d, str)
        and recurrence.weekday(d.strip()) is not None
    ]
    if not pickup_days:
        return

    frequency = str(attrs.get("Frequency", "Weekly")).lower()
    timing_week = str(attrs.get("TimingWeek", "")).lower()

    for day_name in pickup_days:
        for collection_date in _generate_dates(
            day_name,
            frequency,
            timing_week,
            source._today,
            source._end_date,
        ):
            yield Schedule(raw_type, collection_date, count=1)


@final
class Source(BaseSource):
    TITLE = "Community Waste Disposal (CWD)"
    DESCRIPTION = "Source for Community Waste Disposal (CWD) in North Texas"
    URL = "https://www.communitywastedisposal.com"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Forney TX": {"address": "100 Princeton Cir, Forney, TX 75126"},
        "Allen TX": {"address": "123 Main St, Allen, TX 75002"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including city and ZIP "
            "(e.g. '123 Main St, Allen, TX 75002')."
        ),
    }

    retrieve = ArcGis.ArcGisMultiFeatureRetriever(LAYERS, geocode_fields="City")
    parse = ArcGis.ArcGisMultiFeatureParser(first_per_layer=True)
    preprocess = Compose(
        RecurrenceExpander(_describe),
        NewEdgeServices.HolidayDelayShift(community=_community),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())
        self._today = date.today()
        self._end_date = self._today + timedelta(days=365)
