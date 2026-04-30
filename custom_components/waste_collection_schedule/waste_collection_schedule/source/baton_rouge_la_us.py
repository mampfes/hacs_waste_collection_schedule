from datetime import datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Baton Rouge, LA"
DESCRIPTION = "Source for Baton Rouge, LA waste collection."
URL = "https://www.brla.gov/337/Garbage-Collection"
COUNTRY = "us"

TEST_CASES = {
    "City Hall (Fri, Fri, Tue/Fri)": {
        "address": "222 Saint Louis St, Baton Rouge, LA 70802"
    },
    "Mall of Louisiana (Thu, Thu, Mon/Thu)": {
        "address": "6401 Bluebonnet Boulevard, Baton Rouge, LA 70836"
    },
    "Amazon Fulfillment Center (Wed, Sat, Wed/Sat)": {
        "address": "9001 Cortana Pl, Baton Rouge, LA 70815"
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address (e.g. '222 Saint Louis St, Baton Rouge, LA 70802')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

BASE_URL = "https://services.arcgis.com/KYvXadMcgf0K1EzK/arcgis/rest/services/GovernmentServices_WFL1/FeatureServer"
GARBAGE_URL = f"{BASE_URL}/14"
TRASH_URL = f"{BASE_URL}/15"
RECYCLING_URL = f"{BASE_URL}/16"

ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Trash": "mdi:leaf",
    "Recycling": "mdi:recycle",
}

DAY_FIELDS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        entries: list[Collection] = []

        services = [
            (GARBAGE_URL, "Garbage"),
            (TRASH_URL, "Trash"),
            (RECYCLING_URL, "Recycling"),
        ]

        for url, waste_type in services:
            try:
                features = query_feature_layer(
                    url,
                    geometry=location,
                    out_fields="*",
                )

                attrs = features[0]
                # ArcGIS may return field names in varying case (MONDAY vs Monday)
                attrs_upper = {k.upper(): v for k, v in attrs.items()}
                for day in DAY_FIELDS:
                    if (attrs_upper.get(day.upper()) or "").strip().lower() == "yes":
                        entries.extend(self._weekly_dates(day, waste_type))

            except ArcGisError:
                continue

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

        return entries

    @staticmethod
    def _weekly_dates(day_name: str, waste_type: str) -> list[Collection]:
        weekday_idx = WEEKDAYS.get(day_name)
        if weekday_idx is None:
            return []
        today = datetime.now().date()

        days_ahead = (weekday_idx - today.weekday()) % 7
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
