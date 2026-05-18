import datetime
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Taupō District Council"
DESCRIPTION = "Source for Taupō District Council kerbside collection."
URL = "https://www.taupodc.govt.nz"
COUNTRY = "nz"
TEST_CASES = {
    "9 Richmond Avenue Taupo": {"address": "9 Richmond Avenue Taupo"},
    "72 Wharewaka Road Taupo": {"address": "72 Wharewaka Road Taupo"},
    "48 Lake Terrace Taupo": {"address": "48 Lake Terrace Taupo"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address as it appears on the Taupō District Council property map, e.g. '9 Richmond Avenue Taupo'",
    }
}

PROPERTY_URL = "https://maps.taupodc.govt.nz/server/rest/services/property/Rateable_Property/FeatureServer/0/query"
REFUSE_URL = "https://services7.arcgis.com/S7DHOirgbYgdtrbR/arcgis/rest/services/Refuse_Collection/FeatureServer/0/query"

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

ICON_MAP = {
    "Kerbside Collection": "mdi:trash-can",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (waste-collection-schedule)"}


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        # Step 1: Geocode address via Rateable Property layer
        params = {
            "where": f"UPPER(address) LIKE UPPER('%{self._address}%')",
            "outFields": "address,Latitude,Longitude",
            "resultRecordCount": "5",
            "f": "json",
        }
        r = requests.get(PROPERTY_URL, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()

        features = data.get("features", [])
        if not features:
            raise SourceArgumentNotFound("address", self._address)

        # Use the first matching property
        attrs = features[0]["attributes"]
        lat = attrs.get("Latitude")
        lon = attrs.get("Longitude")

        if lat is None or lon is None:
            raise SourceArgumentNotFound("address", self._address)

        # Step 2: Spatial query to find refuse collection zone
        geometry = json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}})
        params = {
            "geometry": geometry,
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "Collection_Day,Location",
            "f": "json",
        }
        r = requests.get(REFUSE_URL, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()

        features = data.get("features", [])
        if not features:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [],
            )

        collection_day = features[0]["attributes"].get("Collection_Day", "")
        if not collection_day:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [],
            )

        # Parse one or two collection days (e.g. "Tuesday & Friday", "Wed & Friday")
        day_names = [d.strip() for d in collection_day.replace("&", ",").split(",")]

        # Normalise abbreviated day names
        abbreviations = {
            "Mon": "Monday",
            "Tue": "Tuesday",
            "Wed": "Wednesday",
            "Thu": "Thursday",
            "Fri": "Friday",
            "Sat": "Saturday",
            "Sun": "Sunday",
        }
        normalised = []
        for d in day_names:
            full = abbreviations.get(d, d)
            if full not in WEEKDAYS:
                continue
            normalised.append(full)

        if not normalised:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [],
            )

        # Step 3: Generate 52 weeks of upcoming dates for each day
        today = datetime.date.today()
        entries = []
        for day_name in normalised:
            target_weekday = WEEKDAYS[day_name]
            days_ahead = (target_weekday - today.weekday()) % 7
            next_date = today + datetime.timedelta(days=days_ahead)
            for _ in range(52):
                entries.append(
                    Collection(
                        date=next_date,
                        t="Kerbside Collection",
                        icon=ICON_MAP["Kerbside Collection"],
                    )
                )
                next_date += datetime.timedelta(weeks=1)

        return entries
