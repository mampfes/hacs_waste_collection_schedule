from __future__ import annotations

from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Sutherland Shire Council"
DESCRIPTION = "Source for Sutherland Shire Council, NSW, Australia."
URL = "https://www.sutherlandshire.nsw.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "5 Cleveland Place, BONNET BAY": {
        "suburb": "BONNET BAY",
        "street": "Cleveland Place",
        "house_number": "5",
    },
    "20 Waratah Street, CRONULLA": {
        "suburb": "CRONULLA",
        "street": "Waratah Street",
        "house_number": "20",
    },
    # The council's own administration building, and the only Zone 1 case
    # here: both of the above are Zone 2, so nothing exercised the other
    # fortnight.
    "4-20 Eton Street, SUTHERLAND": {
        "suburb": "SUTHERLAND",
        "street": "Eton Street",
        "house_number": "4-20",
    },
}

ICON_MAP = {
    "Garbage": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Garden Waste": Icons.GARDEN,
}

PARAM_TRANSLATIONS = {
    "en": {
        "suburb": "Suburb",
        "street": "Street Name",
        "house_number": "House Number",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "suburb": "Suburb, e.g. BONNET BAY.",
        "street": "Street name spelled out in full, e.g. Cleveland Place.",
        "house_number": "House number, e.g. 5.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Use the address exactly as it appears on council correspondence — "
        "street type spelled out in full (Street, Place, Avenue). You can "
        "check your address on the map at "
        "https://www.sutherlandshire.nsw.gov.au/living-here/waste-and-recycling/bin-collection"
    ),
}

# The council's "When is my bin collected?" page is backed by this public
# ArcGIS layer (one feature per property, carrying the collection weekday,
# zone and recycling frequency). The previous ASP.NET dropdown form the old
# scraper drove was removed from the website in 2026, and the site now also
# TLS-fingerprints plain library HTTP clients; the GIS endpoint has neither
# problem.
_ARCGIS_QUERY_URL = (
    "https://geoserver.ssc.nsw.gov.au/arcgis/rest/services/WebOnline/MapServer/4/query"
)

_WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

# The GIS layer gives a property's zone but nothing about which fortnight is
# which, so the alternation needs an anchor. This is the Monday of a week the
# council's own Zone 1 calendar highlights yellow (yellow-lid recycling; green
# highlight is the green-lid garden week):
# https://www.sutherlandshire.nsw.gov.au/__data/assets/pdf_file/0020/121934/SSC-Waste-Calendar-2026-27-Zone1-Print.pdf
_ZONE1_RECYCLING_WEEK = date(2026, 8, 31)

# Whole weeks added before taking the parity. Zone 2's recycling week is Zone
# 1's garden week; the two published calendars are opposite on every one of the
# 260 collection days they cover.
_ZONE_WEEK_OFFSETS: dict[str, int] = {
    "1": 0,
    "2": 1,
}

_SCHEDULE_WEEKS = 52


def _next_weekday(from_date: date, weekday: int) -> date:
    """Return the next occurrence of weekday on or after from_date."""
    days_ahead = weekday - from_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)


def _generate_collections(
    weekday: int, zone: str, start: date, end: date, weekly_recycling: bool
) -> list[Collection]:
    """Generate all collection dates between start and end.

    Garbage is weekly. Recycling and garden waste alternate fortnights by
    zone; properties flagged for weekly recycling (some unit blocks) get
    recycling every week on top of the fortnightly garden collection.
    """
    week_offset = _ZONE_WEEK_OFFSETS.get(zone, 0)
    cur = _next_weekday(start, weekday)
    entries: list[Collection] = []

    while cur <= end:
        entries.append(Collection(date=cur, t="Garbage", icon=ICON_MAP["Garbage"]))

        # The anchor is a Monday, so flooring the day difference by 7 buckets
        # each collection into its own Monday-to-Sunday week.
        week = (cur - _ZONE1_RECYCLING_WEEK).days // 7
        if (week + week_offset) % 2 == 0:
            waste_type = "Recycling"
        else:
            waste_type = "Garden Waste"
            if weekly_recycling:
                entries.append(
                    Collection(date=cur, t="Recycling", icon=ICON_MAP["Recycling"])
                )
        entries.append(Collection(date=cur, t=waste_type, icon=ICON_MAP[waste_type]))

        cur += timedelta(weeks=1)

    return entries


def _sql_quote(value: str) -> str:
    return value.replace("'", "''")


class Source:
    def __init__(self, suburb: str, street: str, house_number: str):
        self._suburb = suburb.upper().strip()
        self._street = street.strip()
        self._house_number = str(house_number).strip()

    def _query(self, where: str, record_count: int = 50) -> list[dict]:
        r = requests.get(
            _ARCGIS_QUERY_URL,
            params={
                "where": where,
                "outFields": "situ1,situ2,DAY_OF_WEEK,ZONE_NO,RECYCLE_PICKUP",
                "returnGeometry": "false",
                "resultRecordCount": str(record_count),
                "f": "json",
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise ValueError(
                f"Sutherland Shire GIS query failed: {data['error'].get('message')}"
            )
        return [f["attributes"] for f in data.get("features", [])]

    def fetch(self) -> list[Collection]:
        address = _sql_quote(f"{self._house_number} {self._street}".upper())
        suburb = _sql_quote(self._suburb)

        features = self._query(
            f"UPPER(situ1) = '{address}' AND UPPER(situ2) LIKE '{suburb}%'"
        )
        if not features:
            # Unit prefixes ("5/20 Waratah Street") and minor spacing quirks.
            features = self._query(
                f"UPPER(situ1) LIKE '{address}%' AND UPPER(situ2) LIKE '{suburb}%'"
            )
        if not features:
            # Nothing for that house number — suggest addresses on the street.
            street_matches = self._query(
                f"UPPER(situ1) LIKE '%{_sql_quote(self._street.upper())}%'"
                f" AND UPPER(situ2) LIKE '{suburb}%'"
            )
            if street_matches:
                raise SourceArgumentNotFoundWithSuggestions(
                    "house_number",
                    self._house_number,
                    sorted({f["situ1"] for f in street_matches}),
                )
            raise SourceArgumentNotFound("street", f"{self._street}, {self._suburb}")

        attrs = features[0]
        day_name = str(attrs.get("DAY_OF_WEEK", "")).strip().lower()
        weekday = _WEEKDAY_MAP.get(day_name)
        if weekday is None:
            raise ValueError(
                f"Unknown collection day {attrs.get('DAY_OF_WEEK')!r} for "
                f"{attrs.get('situ1')}, {attrs.get('situ2')}"
            )
        zone = str(attrs.get("ZONE_NO", "1"))
        weekly_recycling = (
            str(attrs.get("RECYCLE_PICKUP", "")).strip().lower() == "weekly"
        )

        today = date.today()
        end_date = today + timedelta(weeks=_SCHEDULE_WEEKS)
        return _generate_collections(weekday, zone, today, end_date, weekly_recycling)
