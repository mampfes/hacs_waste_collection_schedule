from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Marysville, WA"
DESCRIPTION = "Source for Marysville, WA solid waste collection schedules."
URL = "https://marysvillewa.gov/172/Solid-Waste-Recycling"
COUNTRY = "us"

TEST_CASES = {
    "Marysville City Hall (501 Delta Ave) - Friday weekly": {
        "street_address": "501 Delta Ave"
    },
    "4011 81st Pl NE - Monday weekly": {"street_address": "4011 81st Pl NE"},
    "8507 61st Dr NE - Wednesday monthly": {"street_address": "8507 61st Dr NE"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": (
            "Street address as house number and street name "
            "(e.g. '501 Delta Ave' or '6400 88th St NE'). "
            "Do not include city or ZIP code."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_address": "Street Address",
    },
}

FEATURE_SERVICE_URL = (
    "https://services2.arcgis.com/ZASkNq1SMoPvFBOv/arcgis/rest/services"
    "/Marysville_Solid_Waste_Pickup/FeatureServer/29/query"
)

WEEKS_AHEAD = 26

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
    # Abbreviations found in source data
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "thur": 3,  # codespell:ignore thur
    "thurs": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

ICON_MAP = {
    "Garbage Collection": Icons.GENERAL_WASTE,
}


def _weekly_dates(weekday_idx: int, waste_type: str) -> list[Collection]:
    """Generate WEEKS_AHEAD weekly Collection entries for the given weekday."""
    today = date.today()
    days_ahead = (weekday_idx - today.weekday()) % 7
    first = today + timedelta(days=days_ahead)
    icon = ICON_MAP.get(waste_type)
    return [
        Collection(date=first + timedelta(weeks=i), t=waste_type, icon=icon)
        for i in range(WEEKS_AHEAD)
    ]


def _four_weekly_dates(weekday_idx: int, waste_type: str) -> list[Collection]:
    """Generate ~13 monthly (every-4-weeks) Collection entries for the given weekday."""
    today = date.today()
    days_ahead = (weekday_idx - today.weekday()) % 7
    first = today + timedelta(days=days_ahead)
    icon = ICON_MAP.get(waste_type)
    return [
        Collection(date=first + timedelta(weeks=i * 4), t=waste_type, icon=icon)
        for i in range(WEEKS_AHEAD // 4)
    ]


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address.strip()

    def fetch(self) -> list[Collection]:
        # Build a case-insensitive LIKE query against Service_Address.
        # The DB stores addresses in uppercase; UPPER() on both sides handles
        # any capitalisation the user supplies.
        search = self._street_address.upper().replace("'", "''")
        where = f"UPPER(Service_Address) LIKE '{search}%'"

        params = {
            "where": where,
            "outFields": "Service_Address,Service_Day,Pickup_Frequency",
            "returnGeometry": "false",
            "f": "json",
        }

        r = requests.get(FEATURE_SERVICE_URL, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        if "error" in data:
            raise RuntimeError(f"ArcGIS query error: {data['error']}")

        features = data.get("features", [])
        if not features:
            # Try a contains-search to surface useful address suggestions.
            suggestion_params = {
                "where": f"UPPER(Service_Address) LIKE '%{search}%'",
                "outFields": "Service_Address",
                "returnGeometry": "false",
                "returnDistinctValues": "true",
                "orderByFields": "Service_Address",
                "resultRecordCount": "5",
                "f": "json",
            }
            sr = requests.get(FEATURE_SERVICE_URL, params=suggestion_params, timeout=20)
            suggestions = [
                f["attributes"]["Service_Address"].strip()
                for f in sr.json().get("features", [])
                if f.get("attributes", {}).get("Service_Address")
            ]
            if suggestions:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street_address", self._street_address, suggestions
                )
            raise SourceArgumentNotFound("street_address", self._street_address)

        entries: list[Collection] = []
        for feat in features:
            attrs = feat.get("attributes", {})
            service_day = (attrs.get("Service_Day") or "").strip()
            pickup_freq = (attrs.get("Pickup_Frequency") or "").strip()

            weekday_idx = WEEKDAYS.get(service_day.lower())
            if weekday_idx is None:
                # Unknown day format (e.g. Y/N bitmask edge cases) — skip
                continue

            waste_type = "Garbage Collection"
            if pickup_freq == "EveryWeek":
                entries.extend(_weekly_dates(weekday_idx, waste_type))
            elif pickup_freq == "Monthly":
                entries.extend(_four_weekly_dates(weekday_idx, waste_type))
            else:
                # Unknown frequency; default to weekly
                entries.extend(_weekly_dates(weekday_idx, waste_type))

        if not entries:
            raise SourceArgumentNotFound("street_address", self._street_address)

        return entries
