from __future__ import annotations

from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Sutherland Shire Council"
DESCRIPTION = "Source for Sutherland Shire Council, NSW, Australia."
URL = "https://www.sutherlandshire.nsw.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "5 Cleveland Place, Bonnet Bay": {
        "suburb": "Bonnet Bay",
        "street": "Cleveland Place",
        "house_number": "5",
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
        "suburb": "Suburb name, as normally written (e.g. Bonnet Bay).",
        "street": "Street name, as normally written (e.g. Cleveland Place).",
        "house_number": "House number (e.g. 5).",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your suburb, street name and house number as they normally "
        "appear in your address. These are looked up automatically via the "
        "Sutherland Shire online services map, so they don't need to match "
        "any particular list."
    ),
}

# Public Esri "World" geocoder, used server-side to resolve a free-text
# address to coordinates (no API key required for this endpoint, the same
# service is already used by the cityofparramatta_nsw_gov_au source).
_GEOCODE_URL = (
    "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer"
    "/findAddressCandidates"
)

# ArcGIS layer published by Sutherland Shire Council that returns the
# garbage collection day and recycling/garden-waste zone for a given point.
# Reverse engineered from the "services-map" widget's bundled JavaScript on
# https://www.sutherlandshire.nsw.gov.au/living-here/waste-and-recycling/bin-collection
_ZONE_QUERY_URL = (
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

# Reference Monday used to anchor the fortnightly recycling/garden-waste
# alternation. In the week of this Monday, Zone 2 places out recycling and
# Zone 1 places out garden waste (verified against the council's own
# 2026/27 Zone 1 and Zone 2 collection calendars). The two zones are always
# on opposite fortnights.
_REFERENCE_MONDAY = date(2026, 7, 13)

_SCHEDULE_WEEKS = 52


def _next_weekday(from_date: date, weekday: int) -> date:
    """Return the next occurrence of weekday on or after from_date."""
    days_ahead = weekday - from_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)


def _generate_collections(
    weekday: int, zone_no: int, start: date, end: date
) -> list[Collection]:
    """Generate all collection dates between start and end.

    Recycling and garden waste alternate fortnightly. Which type falls on a
    given occurrence is determined by the number of whole weeks since a fixed
    reference Monday together with the zone number. Zone 2 recycles in the
    reference fortnight; Zone 1 is offset by one week.
    """
    entries: list[Collection] = []
    cur = _next_weekday(start, weekday)

    while cur <= end:
        entries.append(Collection(date=cur, t="Garbage", icon=ICON_MAP["Garbage"]))

        weeks_since_ref = (cur - _REFERENCE_MONDAY).days // 7
        reference_fortnight = weeks_since_ref % 2 == 0
        recycling_this_week = (zone_no == 2) == reference_fortnight
        if recycling_this_week:
            waste_type = "Recycling"
        else:
            waste_type = "Garden Waste"
        entries.append(Collection(date=cur, t=waste_type, icon=ICON_MAP[waste_type]))

        cur += timedelta(weeks=1)

    return entries


class Source:
    def __init__(self, suburb: str, street: str, house_number: str):
        self._suburb = suburb.strip()
        self._street = street.strip()
        self._house_number = str(house_number).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-AU,en;q=0.9",
            }
        )

        address = f"{self._house_number} {self._street}, {self._suburb} NSW, Australia"

        # Step 1: Geocode the address to a lat/lon point.
        geo_params = {
            "f": "json",
            "SingleLine": address,
            "outFields": "Match_addr",
            "maxLocations": "1",
            "sourceCountry": "AUS",
        }
        r_geo = session.get(_GEOCODE_URL, params=geo_params, timeout=30)
        r_geo.raise_for_status()
        candidates = r_geo.json().get("candidates", [])
        if not candidates:
            raise SourceArgumentNotFound(
                "suburb/street/house_number",
                f"{self._house_number} {self._street}, {self._suburb}",
            )

        location = candidates[0].get("location")
        if not location or "x" not in location or "y" not in location:
            raise SourceArgumentNotFound(
                "suburb/street/house_number",
                f"{self._house_number} {self._street}, {self._suburb}",
            )
        lon, lat = location["x"], location["y"]

        # Step 2: Query the council's collection-zone layer for that point.
        zone_params = {
            "f": "json",
            "geometry": f"{lon},{lat}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "units": "esriSRUnit_Meter",
            "outFields": "*",
            "returnGeometry": "false",
        }
        r_zone = session.get(
            _ZONE_QUERY_URL,
            params=zone_params,
            headers={
                "Referer": (
                    "https://www.sutherlandshire.nsw.gov.au/living-here/"
                    "waste-and-recycling/bin-collection"
                )
            },
            timeout=30,
        )
        r_zone.raise_for_status()
        features = r_zone.json().get("features", [])
        if not features:
            raise SourceArgumentNotFound(
                "suburb/street/house_number",
                f"{self._house_number} {self._street}, {self._suburb}",
            )

        attributes = features[0].get("attributes", {})
        day_of_week = attributes.get("DAY_OF_WEEK")
        zone_no = attributes.get("ZONE_NO")
        if not day_of_week or zone_no not in (1, 2):
            raise SourceArgumentNotFound(
                "suburb/street/house_number",
                f"{self._house_number} {self._street}, {self._suburb}",
            )

        weekday = _WEEKDAY_MAP.get(str(day_of_week).strip().lower())
        if weekday is None:
            raise SourceArgumentNotFound(
                "suburb/street/house_number",
                f"{self._house_number} {self._street}, {self._suburb}",
            )

        today = date.today()
        end_date = today + timedelta(weeks=_SCHEDULE_WEEKS)
        return _generate_collections(weekday, zone_no, today, end_date)
