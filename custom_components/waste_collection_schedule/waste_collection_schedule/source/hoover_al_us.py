from datetime import datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Hoover, AL"
DESCRIPTION = "Source for Hoover, AL garbage collection."
URL = "https://hooveralabama.gov"
COUNTRY = "us"

TEST_CASES = {
    "Tyler Rd (Mon/Thu)": {"address": "2255 Tyler Rd, Hoover, AL"},
    "Cobblestone Ln (Tue/Fri)": {"address": "101 Cobblestone Ln, Hoover, AL"},
}

ICON_MAP = {
    "Garbage": "mdi:trash-can",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address (e.g. '2255 Tyler Rd, Hoover, AL')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

GARBAGE_ZONE_URL = "https://services8.arcgis.com/LmhR4UJYxC4YhccG/arcgis/rest/services/Hoover_Garbage_Pickup_WFL1/FeatureServer/2"

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
}


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
            features = query_feature_layer(GARBAGE_ZONE_URL, geometry=location)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        attrs = features[0]
        trashday = (attrs.get("Trashday") or "").strip()
        if not trashday:
            raise SourceArgumentNotFound("address", self._address)

        # Parse "Monday / Thursday" or "Tuesday / Friday"
        days = [d.strip() for d in trashday.split("/")]

        entries: list[Collection] = []
        for day_name in days:
            if day_name in WEEKDAYS:
                entries.extend(self._weekly_dates(day_name, "Garbage"))

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

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
