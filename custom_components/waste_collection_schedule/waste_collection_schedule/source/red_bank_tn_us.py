import datetime
import json
import re
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE

# City of Red Bank, TN "trash day" ArcGIS FeatureServer: layer 1 holds parcels
# (STNUM/STNAME, one polygon per address), layers 2-6 are the Monday..Friday
# collection-zone polygons. The flow is where-clause -> centroid (a
# ``returnCentroid=true`` attribute query, raising on no match or on an
# ambiguous multi-parcel address) -> a spatial COUNT-only query against each
# day-zone layer in turn, stopping at the first with a non-zero count.
# feature_query()/ArcGisFeatureRetriever don't expose ``returnCentroid`` or a
# count-only query, so this is a source-defined retrieve() (via
# source.session) rather than the shared ArcGIS retriever pair; the resolved
# weekday is then handed to the framework's recurrence + holiday helpers.

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

_TYPE_MAP = {"Trash": GENERAL_WASTE}

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


def _red_bank_holiday_set(years) -> set:
    """No-collection weekdays: US federal holidays per Tennessee's calendar
    (adds Good Friday, drops Columbus Day, which the city does not observe),
    plus the day after Thanksgiving."""
    days = recurrence.us_federal_holidays(years, subdiv="TN")
    for year in years:
        thanksgiving = recurrence.monthly_nth_weekday(
            3, 4, on_or_after=datetime.date(year, 11, 1)
        )
        days.add(thanksgiving + datetime.timedelta(days=1))
    return days


def _describe(record: dict, source: Any):
    today = datetime.date.today()
    end = today + datetime.timedelta(days=HORIZON_DAYS)
    # This calendar week's occurrence of the collection weekday (which may
    # already have passed this week) starts the weekly cadence, matching the
    # legacy source's own base-line calculation.
    week_start = today - datetime.timedelta(days=today.weekday())
    first = week_start + datetime.timedelta(days=record["weekday"])
    yield Schedule("Trash", first, recurrence.WEEKLY, until=end)


def _adjust(collection_date: datetime.date, key: str, source: Any):
    """Delay onto the next weekday that is neither a weekend day nor a
    no-collection holiday (chained: a bump that lands on another holiday or a
    weekend keeps moving forward), matching the legacy source exactly."""
    holidays = source._holidays
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

    PARAMS = (text_field("street_address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as it appears in Red Bank (e.g. '1107 "
            "Ashmore Ave'). The city/state/ZIP are optional. Your collection "
            "weekday is looked up from the city's official trash-day map."
        ),
    }

    preprocess = Compose(RecurrenceExpander(_describe), HolidayShift(_adjust))
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, street_address: str):
        super().__init__(street_address=street_address.strip())

    def retrieve(self, source: "Source"):
        address = source.params["street_address"]
        stnum, street_name = _parse_street_address(address)
        if not stnum or not street_name:
            raise SourceArgumentNotFound("street_address", address)

        esc = street_name.replace("'", "''")
        where = f"STNUM='{stnum}' AND UPPER(STNAME) LIKE '{esc}%'"

        resp = source.session.get(
            f"{FEATURE_SERVER}/{PARCELS_LAYER}/query",
            params={
                "f": "json",
                "where": where,
                "outFields": "ADDRESS,STNUM,STNAME",
                "returnGeometry": "false",
                "returnCentroid": "true",
                "resultRecordCount": 50,
            },
            timeout=30,
        )
        resp.raise_for_status()
        features = resp.json().get("features", [])
        if not features:
            raise SourceArgumentNotFound("street_address", address)

        # collapse multi-polygon parcels that share one address
        by_address: dict = {}
        for feat in features:
            addr = feat.get("attributes", {}).get("ADDRESS") or ""
            by_address.setdefault(addr, feat)

        if len(by_address) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "street_address", address, sorted(by_address.keys())
            )

        feat = next(iter(by_address.values()))
        centroid = feat.get("centroid")
        if not centroid:
            raise SourceArgumentNotFound("street_address", address)

        geometry = json.dumps(
            {
                "x": centroid["x"],
                "y": centroid["y"],
                "spatialReference": {"wkid": WKID},
            }
        )
        weekday = None
        for layer_id, wd in DAY_LAYERS.items():
            r = source.session.get(
                f"{FEATURE_SERVER}/{layer_id}/query",
                params={
                    "f": "json",
                    "geometry": geometry,
                    "geometryType": "esriGeometryPoint",
                    "inSR": WKID,
                    "spatialRel": "esriSpatialRelIntersects",
                    "where": "1=1",
                    "returnCountOnly": "true",
                },
                timeout=30,
            )
            r.raise_for_status()
            if r.json().get("count", 0) > 0:
                weekday = wd
                break
        if weekday is None:
            raise SourceArgumentNotFound("street_address", address)

        today = datetime.date.today()
        end = today + datetime.timedelta(days=HORIZON_DAYS)
        # Stashed on the source instance for HolidayShift's _adjust() to read.
        source._holidays = _red_bank_holiday_set(range(today.year, end.year + 2))

        return [{"weekday": weekday}]

    def parse(self, raw, source: "Source | None" = None):
        return raw
