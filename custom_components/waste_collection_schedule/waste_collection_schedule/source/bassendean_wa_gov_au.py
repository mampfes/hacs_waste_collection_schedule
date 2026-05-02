from datetime import date, datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Town of Bassendean"
DESCRIPTION = "Source for Town of Bassendean waste collection."
URL = "https://www.bassendean.wa.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "Kenny St": {"address": "16 Kenny St, Bassendean"},
    "Broadway": {"address": "50 Broadway, Bassendean"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "FOGO": "mdi:leaf",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address (e.g. '16 Kenny St, Bassendean')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

FEATURE_URL = "https://services-ap1.arcgis.com/551UnqKK1GZeDKxQ/arcgis/rest/services/address_lookup_for_bin_days_dissolved/FeatureServer/0"

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
}

# Base dates for fortnightly schedules, extracted from the ArcGIS Arcade
# expressions in the web map config. General Waste and Recycling alternate
# on opposite fortnights.
GENERAL_WASTE_BASE: dict[str, date] = {
    "Monday": date(2025, 3, 28),
    "Tuesday": date(2025, 3, 29),
    "Wednesday": date(2025, 3, 30),
    "Thursday": date(2025, 4, 1),
    "Friday": date(2025, 4, 2),
}

RECYCLING_BASE: dict[str, date] = {
    "Monday": date(2025, 3, 21),
    "Tuesday": date(2025, 3, 22),
    "Wednesday": date(2025, 3, 23),
    "Thursday": date(2025, 3, 24),
    "Friday": date(2025, 3, 25),
}


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
            features = query_feature_layer(FEATURE_URL, geometry=location)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        attrs = features[0]
        service_day = attrs.get("ServiceDay", "").strip()
        if not service_day or service_day not in WEEKDAYS:
            raise SourceArgumentNotFound("address", self._address)

        entries: list[Collection] = []

        # FOGO — weekly
        entries.extend(self._weekly_dates(service_day, "FOGO"))

        # General Waste — fortnightly
        base = GENERAL_WASTE_BASE.get(service_day)
        if base:
            entries.extend(self._fortnightly_dates(base, "General Waste"))

        # Recycling — fortnightly
        base = RECYCLING_BASE.get(service_day)
        if base:
            entries.extend(self._fortnightly_dates(base, "Recycling"))

        return entries

    @staticmethod
    def _weekly_dates(day_name: str, waste_type: str) -> list[Collection]:
        weekday = WEEKDAYS[day_name]
        today = datetime.now().date()
        days_ahead = (weekday - today.weekday()) % 7
        next_date = today + timedelta(days=days_ahead)
        icon = ICON_MAP.get(waste_type)
        return [
            Collection(
                date=next_date + timedelta(weeks=i),
                t=waste_type,
                icon=icon,
            )
            for i in range(26)
        ]

    @staticmethod
    def _fortnightly_dates(base_date: date, waste_type: str) -> list[Collection]:
        today = datetime.now().date()
        next_date = base_date
        while next_date < today:
            next_date += timedelta(days=14)
        icon = ICON_MAP.get(waste_type)
        return [
            Collection(
                date=next_date + timedelta(days=i * 14),
                t=waste_type,
                icon=icon,
            )
            for i in range(13)
        ]
