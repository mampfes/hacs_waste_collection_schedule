import datetime
import json
import re

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)

TITLE = "Red Bank, Tennessee"
DESCRIPTION = "Source for residential trash collection in the City of Red Bank, TN."
URL = "https://www.redbanktn.gov/257/Solid-Waste"
COUNTRY = "us"
TEST_CASES = {
    "Monday route": {"street_address": "1107 Ashmore Ave"},
    "Tuesday route": {"street_address": "3121 Dayton Blvd"},
    "Friday route": {"street_address": "145 Ivy Row Ln"},
    "With city/state/zip": {"street_address": "20 Mason Dr, Red Bank, TN 37415"},
}

# Public, token-free ArcGIS Feature Service backing the city's "trash day" map.
# Layer 1  = parcels (each carries STNUM / STNAME / ADDRESS, polygon geometry).
# Layers 2-6 = the Monday..Friday collection-zone polygons.
_FEATURE_SERVER = (
    "https://services9.arcgis.com/b7VbpZSIoQ7S1Sl6/arcgis/rest/services/"
    "Red_Bank_Garbage_Pickup_Schedule_WFL1/FeatureServer"
)
_PARCELS_LAYER = 1
# day-zone layer id -> Python weekday() index (Mon=0 .. Fri=4)
_DAY_LAYERS = {2: 0, 3: 1, 4: 2, 5: 3, 6: 4}
_WKID = 102100  # Web Mercator, the service's native spatial reference

# How far ahead to project the recurring weekly schedule.
_HORIZON_DAYS = 365

ICON_MAP = {
    "Trash": Icons.GENERAL_WASTE,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your street address as it appears in Red Bank (e.g. '1107 Ashmore "
        "Ave'). The city/state/ZIP are optional. Your collection weekday is looked "
        "up from the city's official trash-day map."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": "Street address within the City of Red Bank, TN.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_address": "Street Address",
    },
}

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


def _easter(year: int) -> datetime.date:
    """Gregorian Easter Sunday (Anonymous algorithm)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(year, month, day)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> datetime.date:
    """Date of the n-th given weekday (Mon=0) in a month."""
    first = datetime.date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + datetime.timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> datetime.date:
    """Date of the last given weekday (Mon=0) in a month."""
    if month == 12:
        nxt = datetime.date(year + 1, 1, 1)
    else:
        nxt = datetime.date(year, month + 1, 1)
    last = nxt - datetime.timedelta(days=1)
    return last - datetime.timedelta(days=(last.weekday() - weekday) % 7)


def _observed_weekday(d: datetime.date) -> datetime.date:
    """City observes a weekend fixed-date holiday on the adjacent weekday."""
    if d.weekday() == 5:  # Saturday -> Friday before
        return d - datetime.timedelta(days=1)
    if d.weekday() == 6:  # Sunday -> Monday after
        return d + datetime.timedelta(days=1)
    return d


def _red_bank_holidays(year: int) -> set:
    """Weekdays the City of Red Bank does not collect, per its published
    holiday schedule (federal holidays + Good Friday + day after Thanksgiving).

    Note: in some years the city additionally closes the day before/after
    Christmas and New Year's, which is announced ad hoc and not modelled here;
    such weeks may differ by a day from the city's posted makeup table.
    """
    h = set()
    for month, day in ((1, 1), (6, 19), (7, 4), (11, 11), (12, 25)):
        h.add(_observed_weekday(datetime.date(year, month, day)))
    h.add(_nth_weekday(year, 1, 0, 3))  # MLK Jr Day (3rd Mon Jan)
    h.add(_nth_weekday(year, 2, 0, 3))  # Presidents Day (3rd Mon Feb)
    h.add(_last_weekday(year, 5, 0))  # Memorial Day (last Mon May)
    h.add(_nth_weekday(year, 9, 0, 1))  # Labor Day (1st Mon Sep)
    thanksgiving = _nth_weekday(year, 11, 3, 4)  # 4th Thu Nov
    h.add(thanksgiving)
    h.add(thanksgiving + datetime.timedelta(days=1))  # day after Thanksgiving
    h.add(_easter(year) - datetime.timedelta(days=2))  # Good Friday
    return h


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address.strip()

    def _parse_address(self) -> tuple:
        """Split a free-text address into (house number, bare street name)."""
        text = self._street_address.split(",")[0].upper()
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

    def _find_centroid(self, session: requests.Session) -> dict:
        stnum, street_name = self._parse_address()
        if not stnum or not street_name:
            raise SourceArgumentNotFound("street_address", self._street_address)

        # escape single quotes for the SQL-style where clause
        esc = street_name.replace("'", "''")
        where = f"STNUM='{stnum}' AND UPPER(STNAME) LIKE '{esc}%'"

        r = session.get(
            f"{_FEATURE_SERVER}/{_PARCELS_LAYER}/query",
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
        r.raise_for_status()
        features = r.json().get("features", [])
        if not features:
            raise SourceArgumentNotFound("street_address", self._street_address)

        # collapse multi-polygon parcels that share one address
        by_address: dict = {}
        for feat in features:
            addr = feat.get("attributes", {}).get("ADDRESS") or ""
            by_address.setdefault(addr, feat)

        if len(by_address) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "street_address",
                self._street_address,
                sorted(by_address.keys()),
            )

        feat = next(iter(by_address.values()))
        centroid = feat.get("centroid")
        if not centroid:
            raise SourceArgumentNotFound("street_address", self._street_address)
        return centroid

    def _weekday_for_centroid(self, session: requests.Session, centroid: dict) -> int:
        geometry = json.dumps(
            {
                "x": centroid["x"],
                "y": centroid["y"],
                "spatialReference": {"wkid": _WKID},
            }
        )
        for layer_id, weekday in _DAY_LAYERS.items():
            r = session.get(
                f"{_FEATURE_SERVER}/{layer_id}/query",
                params={
                    "f": "json",
                    "geometry": geometry,
                    "geometryType": "esriGeometryPoint",
                    "inSR": _WKID,
                    "spatialRel": "esriSpatialRelIntersects",
                    "where": "1=1",
                    "returnCountOnly": "true",
                },
                timeout=30,
            )
            r.raise_for_status()
            if r.json().get("count", 0) > 0:
                return weekday
        # parcel exists but isn't covered by any day zone
        raise SourceArgumentNotFound("street_address", self._street_address)

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        centroid = self._find_centroid(session)
        weekday = self._weekday_for_centroid(session, centroid)

        today = datetime.date.today()
        end = today + datetime.timedelta(days=_HORIZON_DAYS)

        holidays: set = set()
        for year in range(today.year, end.year + 2):
            holidays |= _red_bank_holidays(year)

        icon = ICON_MAP["Trash"]
        entries = []
        # start from this week's occurrence of the collection weekday
        current = (
            today
            - datetime.timedelta(days=today.weekday())
            + datetime.timedelta(days=weekday)
        )
        while current <= end:
            collection_date = current
            # delay onto the next non-holiday weekday (Mon-Fri)
            while collection_date.weekday() >= 5 or collection_date in holidays:
                collection_date += datetime.timedelta(days=1)
            entries.append(Collection(date=collection_date, t="Trash", icon=icon))
            current += datetime.timedelta(weeks=1)

        return entries
