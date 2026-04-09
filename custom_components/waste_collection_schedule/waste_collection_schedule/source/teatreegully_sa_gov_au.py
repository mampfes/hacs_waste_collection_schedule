from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "City of Tea Tree Gully"
DESCRIPTION = "Source for City of Tea Tree Gully waste collection."
URL = "https://www.teatreegully.sa.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "Erica Street": {"address": "4 Erica Street, Tea Tree Gully"},
    "Smart Road": {"address": "1 Smart Road, Modbury"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Organics": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address (e.g. '4 Erica Street, Tea Tree Gully'). "
    "Search at https://www.teatreegully.sa.gov.au/services/bins-and-waste/bin-collection-days",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address (e.g. '4 Erica Street, Tea Tree Gully')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

GEOCODE_URL = "https://utility.arcgis.com/usrsvcs/servers/5c770a0bb67f4b8d893e21dccad13b70/rest/services/World/GeocodeServer/findAddressCandidates"
ZONE_URL = "https://services9.arcgis.com/CsUMpO9iTKFFwe1O/arcgis/rest/services/Waste_View_Public/FeatureServer/4/query"

# Reference: Monday 5 Jan 2025 = Week A
REF_DATE = date(2025, 1, 5)

# JS-style day numbering (Sunday=0) used for offset from reference date
WEEKDAY_OFFSET = {
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6,
    "Sunday": 0,
}

# Public holidays where collection shifts to the next day (from functions.js)
HOLIDAYS = {
    date(2025, 1, 1),
    date(2025, 1, 2),
    date(2025, 1, 3),
    date(2025, 4, 18),
    date(2025, 12, 25),
    date(2025, 12, 26),
    date(2026, 1, 1),
    date(2026, 1, 2),
    date(2026, 4, 3),
    date(2026, 12, 25),
    date(2027, 1, 1),
    date(2027, 3, 26),
    date(2027, 12, 25),
    date(2028, 1, 1),
    date(2028, 4, 14),
    date(2028, 12, 25),
    date(2028, 12, 26),
    date(2028, 12, 27),
    date(2028, 12, 28),
    date(2028, 12, 29),
}


def _adjust_holiday(d: date) -> date:
    """Shift collection date forward by one day if it falls on a holiday."""
    if d in HOLIDAYS:
        return d + timedelta(days=1)
    return d


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        # Step 1: Geocode address
        r = requests.get(
            GEOCODE_URL,
            params={
                "SingleLine": self._address,
                "forStorage": "false",
                "maxLocations": "6",
                "outFields": "*",
                "outSR": '{"wkid":4326}',
                "f": "json",
            },
            headers={
                "Referer": "https://survey123.arcgis.com/",
            },
            timeout=30,
        )
        r.raise_for_status()
        candidates = r.json().get("candidates", [])
        if not candidates:
            raise SourceArgumentNotFound("address", self._address)

        location = candidates[0]["location"]

        # Step 2: Query waste collection zone
        r = requests.get(
            ZONE_URL,
            params={
                "where": "1=1",
                "geometry": f'{{"x": {location["x"]}, "y": {location["y"]}}}',
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "Collection,Week",
                "returnGeometry": "false",
                "resultRecordCount": "1",
                "f": "json",
            },
            headers={
                "Referer": "https://survey123.arcgis.com/",
            },
            timeout=30,
        )
        r.raise_for_status()
        features = r.json().get("features", [])
        if not features:
            raise SourceArgumentNotFound("address", self._address)

        attrs = features[0]["attributes"]
        collection_day = attrs["Collection"]
        week_letter = attrs["Week"]

        day_offset = WEEKDAY_OFFSET.get(collection_day)
        if day_offset is None:
            raise SourceArgumentNotFound("address", self._address)

        # Step 3: Generate collection dates
        # JS-style offsets from REF_DATE (Monday Jan 5, 2025)
        week_a_start = REF_DATE + timedelta(days=day_offset)
        week_b_start = REF_DATE + timedelta(days=7 + day_offset)

        # Determine which fortnightly week gets recycling vs organics
        if week_letter == "A":
            recycling_start = week_a_start
        else:
            recycling_start = week_b_start

        # Find next collection day from today (using Python weekday)
        py_weekday = (day_offset - 1) % 7  # convert JS Sunday=0 to Python Monday=0
        today = date.today()
        days_until = (py_weekday - today.weekday() + 7) % 7
        next_day = today + timedelta(days=days_until)

        entries = []
        for i in range(26):  # ~6 months of weekly collections
            collection_date = next_day + timedelta(weeks=i)
            adjusted = _adjust_holiday(collection_date)

            # General Waste: every week
            entries.append(
                Collection(
                    date=adjusted, t="General Waste", icon=ICON_MAP["General Waste"]
                )
            )

            # Check if this is a recycling or organics week
            days_from_recycling = (collection_date - recycling_start).days
            if days_from_recycling % 14 == 0:
                entries.append(
                    Collection(date=adjusted, t="Recycling", icon=ICON_MAP["Recycling"])
                )
            else:
                entries.append(
                    Collection(date=adjusted, t="Organics", icon=ICON_MAP["Organics"])
                )

        return entries
