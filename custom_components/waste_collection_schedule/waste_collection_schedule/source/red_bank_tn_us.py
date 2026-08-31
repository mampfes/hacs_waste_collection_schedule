import datetime
import re
from functools import lru_cache
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service import ArcGis
from waste_collection_schedule.transformers import ICSTransformer

# City of Red Bank, TN "trash day" ArcGIS FeatureServer: layer 1 holds parcels
# (STNUM/STNAME, one polygon per address), layers 2-6 are the Monday..Friday
# collection-zone polygons. The city's own parcel layer is the geocoder
# (ArcGis.parcel_centroid: a where clause plus returnCentroid, collapsing the
# several polygons one address can have and refusing an address that matched
# two properties), and the day-zone layers are then scanned in order with
# count-only spatial queries until one contains that point. The weekday that
# layer stands for is handed to the framework's recurrence + holiday helpers.

FEATURE_SERVER = (
    "https://services9.arcgis.com/b7VbpZSIoQ7S1Sl6/arcgis/rest/services/"
    "Red_Bank_Garbage_Pickup_Schedule_WFL1/FeatureServer"
)
PARCELS_LAYER = 1
# day-zone layer id -> Python weekday() index (Mon=0 .. Fri=4)
DAY_LAYERS = {2: 0, 3: 1, 4: 2, 5: 3, 6: 4}
WKID = 102100  # Web Mercator, the service's native spatial reference

# How far ahead to project the recurring weekly schedule.
HORIZON_DAYS = 365

_TYPE_MAP = {"Trash": wt.GENERAL_WASTE}

# Street-type suffixes dropped before matching so 'Ave' vs 'Avenue' etc. don't
# cause a miss (the parcel layer stores the bare street name in STNAME).
_SUFFIXES = {
    "ST",
    "STREET",
    "AVE",
    "AVENUE",
    "RD",
    "ROAD",
    "DR",
    "DRIVE",
    "LN",
    "LANE",
    "BLVD",
    "BOULEVARD",
    "CT",
    "COURT",
    "PL",
    "PLACE",
    "TER",
    "TERR",
    "TERRACE",
    "CIR",
    "CIRCLE",
    "WAY",
    "PKWY",
    "PARKWAY",
    "HWY",
    "HIGHWAY",
    "TRL",
    "TRAIL",
    "ROW",
    "PT",
    "POINT",
    "LOOP",
    "RUN",
    "PASS",
    "COVE",
    "CV",
    "XING",
    "CROSSING",
    "SQ",
    "SQUARE",
    "PIKE",
    "PARK",
}
_UNIT_MARKERS = {"APT", "UNIT", "STE", "SUITE", "LOT", "#"}


def _parse_street_address(street_address: str) -> tuple:
    """Split a free-text address into (house number, bare street name)."""
    text = street_address.split(",")[0].upper()
    text = re.sub(r"[^0-9A-Z ]", " ", text)
    tokens = [t for t in text.split() if t]

    stnum = None
    rest = []
    for token in tokens:
        if stnum is None and any(ch.isdigit() for ch in token):
            stnum = token
        elif stnum is not None:
            rest.append(token)

    # drop unit designators and a trailing street-type suffix
    cleaned = []
    skip_next = False
    for token in rest:
        if skip_next:
            skip_next = False
            continue
        if token in _UNIT_MARKERS:
            skip_next = True
            continue
        cleaned.append(token)
    if cleaned and cleaned[-1] in _SUFFIXES:
        cleaned = cleaned[:-1]

    return stnum, " ".join(cleaned)


def _parcel_where(**params: Any) -> str:
    """The parcel-layer clause for the configured address."""
    address = params["street_address"]
    stnum, street_name = _parse_street_address(address)
    if not stnum or not street_name:
        raise SourceArgumentNotFound("street_address", address)
    esc = street_name.replace("'", "''")
    return f"STNUM='{stnum}' AND UPPER(STNAME) LIKE '{esc}%'"


@lru_cache(maxsize=4)
def _red_bank_holiday_set(first_year: int, last_year: int) -> frozenset:
    """No-collection weekdays: US federal holidays per Tennessee's calendar
    (adds Good Friday, drops Columbus Day, which the city does not observe),
    plus the day after Thanksgiving."""
    years = range(first_year, last_year)
    days = set(recurrence.us_federal_holidays(years, subdiv="TN"))
    for year in years:
        thanksgiving = recurrence.monthly_nth_weekday(
            3, 4, on_or_after=datetime.date(year, 11, 1)
        )
        days.add(thanksgiving + datetime.timedelta(days=1))
    return frozenset(days)


def _holidays() -> frozenset:
    today = datetime.date.today()
    end = today + datetime.timedelta(days=HORIZON_DAYS)
    return _red_bank_holiday_set(today.year, end.year + 2)


def _describe(record: tuple, source: Any):
    weekday, _count = record
    today = datetime.date.today()
    end = today + datetime.timedelta(days=HORIZON_DAYS)
    # This calendar week's occurrence of the collection weekday (which may
    # already have passed this week) starts the weekly cadence, matching the
    # legacy source's own base-line calculation.
    week_start = today - datetime.timedelta(days=today.weekday())
    first = week_start + datetime.timedelta(days=weekday)
    yield Schedule("Trash", first, recurrence.WEEKLY, until=end)


def _adjust(collection_date: datetime.date, key: str, source: Any):
    """Delay onto the next weekday that is neither a weekend day nor a
    no-collection holiday (chained: a bump that lands on another holiday or a
    weekend keeps moving forward)."""
    holidays = _holidays()
    while collection_date.weekday() >= 5 or collection_date in holidays:
        collection_date += datetime.timedelta(days=1)
    return collection_date


@final
class Source(BaseSource):
    TITLE = "Red Bank, Tennessee"
    DESCRIPTION = "Source for residential trash collection in the City of Red Bank, TN."
    URL = "https://www.redbanktn.gov/257/Solid-Waste"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Monday route": {"street_address": "1107 Ashmore Ave"},
        "Tuesday route": {"street_address": "3121 Dayton Blvd"},
        "Friday route": {"street_address": "145 Ivy Row Ln"},
        "With city/state/zip": {"street_address": "20 Mason Dr, Red Bank, TN 37415"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as it appears in Red Bank (e.g. '1107 "
            "Ashmore Ave'). The city/state/ZIP are optional. Your collection "
            "weekday is looked up from the city's official trash-day map."
        ),
    }

    retrieve = ArcGis.ArcGisMultiFeatureRetriever(
        [
            (weekday, f"{FEATURE_SERVER}/{layer_id}")
            for layer_id, weekday in DAY_LAYERS.items()
        ],
        point=ArcGis.parcel_centroid(
            f"{FEATURE_SERVER}/{PARCELS_LAYER}",
            where=_parcel_where,
            argument="street_address",
            disambiguate_by="ADDRESS",
            out_fields="ADDRESS,STNUM,STNAME",
            result_record_count=50,
            wkid=WKID,
            timeout=30,
        ),
        where="1=1",
        in_sr=WKID,
        count_only=True,
        first_match=True,
        argument="street_address",
        timeout=30,
    )
    parse = ArcGis.ArcGisMultiFeatureParser(count_only=True)
    preprocess = Compose(RecurrenceExpander(_describe), HolidayShift(_adjust))
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
