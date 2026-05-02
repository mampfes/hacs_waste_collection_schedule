import urllib.parse
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "City of Parramatta"
DESCRIPTION = "Source script for cityofparramatta.nsw.gov.au"
URL = "https://www.cityofparramatta.nsw.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "126 Church Street": {"address": "126 Church Street Parramatta"},
}

PARAM_TRANSLATIONS = {
    "en": {"address": "Address"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full address including suburb (e.g. '126 Church Street Parramatta')"
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your full address including the suburb. Example: `126 Church Street Parramatta`",
}

API_MAP_URL = "https://services6.arcgis.com/NrOjMi9LSYL3MUze/arcgis/rest/services/CoP_Garbage_Recyle_July2021/FeatureServer/0/query"
GEOCODE_URL = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"

ICON_MAP = {
    "General Waste (Red Bin)": "mdi:trash-can",
    "Recycling (Yellow Bin)": "mdi:recycle",
    "Garden Organics (Green Bin)": "mdi:leaf",
}

# The reference date points to a known Monday for an "Area 1" Recycling week.
# Adjust this if the parity is wrong. Area 2 will be the week after.
REFERENCE_DATE_AREA_1_RECYCLING = datetime(2024, 1, 1).date()


class Source:
    def __init__(self, address):
        self._address = address

    def get_collection_dates(self, collection_day_str, is_area_1, is_recycling):
        # Determine 0-6 weekday
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        if collection_day_str not in weekdays:
            return []

        target_wday = weekdays.index(collection_day_str)
        today = datetime.now().date()

        # Calculate days until the next occurrence of this weekday
        days_until = (target_wday - today.weekday() + 7) % 7
        next_date = today + timedelta(days=days_until)

        # Decide the reference week for this bin and area
        # For Parramatta, FOGO and Recycling are alternating weeks.
        # Area 1: Recycling Week X, FOGO Week X+1
        # Area 2: Recycling Week X+1, FOGO Week X

        # Base reference date
        ref_base = REFERENCE_DATE_AREA_1_RECYCLING

        # If it's Area 2, shift the reference for Recycling by 7 days
        if not is_area_1:
            ref_base += timedelta(days=7)

        # If it's FOGO (not recycling), shift by 7 days to alternate
        if not is_recycling:
            ref_base += timedelta(days=7)

        # Calculate full weeks between ref_base and next_date
        days_diff = (next_date - ref_base).days

        # If the number of weeks is odd, it's the wrong week, so add 7 days
        if (days_diff // 7) % 2 != 0:
            next_date += timedelta(days=7)

        return [
            next_date,
            next_date + timedelta(days=14),
            next_date + timedelta(days=28),
        ]

    def fetch(self):
        address = urllib.parse.quote(self._address)

        # 1. Geocode the address to find coordinates
        geo_params = {
            "f": "json",
            "SingleLine": address,
            "outFields": "Match_addr",
            "maxLocations": "1",
        }
        r_geo = requests.get(GEOCODE_URL, params=geo_params, timeout=30)
        r_geo.raise_for_status()

        candidates = r_geo.json().get("candidates", [])
        if not candidates:
            raise SourceArgumentNotFound("address", self._address)

        location = candidates[0].get("location")
        if not location:
            raise SourceArgumentNotFound("address", self._address)

        lat, lon = location["y"], location["x"]

        # 2. Query Parramatta Map API
        # Using spatial relationship 'Intersects' with the point geometry
        api_params = {
            "f": "json",
            "outFields": "*",
            "returnGeometry": "false",
            "spatialRel": "esriSpatialRelIntersects",
            "geometryType": "esriGeometryPoint",
            "geometry": f"{lon},{lat}",
            "inSR": "4326",  # Standard lat/long WKID
        }

        r_api = requests.get(API_MAP_URL, params=api_params, timeout=30)
        r_api.raise_for_status()

        features = r_api.json().get("features", [])
        if not features:
            raise SourceArgumentNotFound("address", self._address)

        properties = features[0].get("attributes", {})

        collection_day = properties.get("DAY", "").strip().capitalize()
        week_str = properties.get("WEEK", "").strip().lower()

        if not collection_day or not week_str:
            raise SourceArgumentNotFound("address", self._address)

        is_area_1 = "area 1" in week_str

        entries = []

        today = datetime.now().date()
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        target_wday = weekdays.index(collection_day)

        # General Waste is weekly
        days_until_general = (target_wday - today.weekday() + 7) % 7
        next_general = today + timedelta(days=days_until_general)
        for i in range(4):
            entries.append(
                Collection(
                    date=next_general + timedelta(days=i * 7),
                    t="General Waste (Red Bin)",
                    icon=ICON_MAP.get("General Waste (Red Bin)"),
                )
            )

        # Recycling (Fortnightly)
        recycling_dates = self.get_collection_dates(
            collection_day, is_area_1, is_recycling=True
        )
        for d in recycling_dates:
            entries.append(
                Collection(
                    date=d,
                    t="Recycling (Yellow Bin)",
                    icon=ICON_MAP.get("Recycling (Yellow Bin)"),
                )
            )

        # Garden Organics / FOGO (Alternate Fortnightly)
        fogo_dates = self.get_collection_dates(
            collection_day, is_area_1, is_recycling=False
        )
        for d in fogo_dates:
            entries.append(
                Collection(
                    date=d,
                    t="Garden Organics (Green Bin)",
                    icon=ICON_MAP.get("Garden Organics (Green Bin)"),
                )
            )

        return entries
