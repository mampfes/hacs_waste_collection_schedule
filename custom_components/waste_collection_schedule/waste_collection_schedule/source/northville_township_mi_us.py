from datetime import datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisQueryError,
    query_feature_layer,
)

TITLE = "Northville Township, MI"
DESCRIPTION = "Source for Northville Township, MI waste collection."
URL = "https://www.twp.northville.mi.us"
COUNTRY = "us"

TEST_CASES = {
    "Northville Rd": {"address": "16795 Northville Rd"},
    "6 Mile Rd": {"address": "39715 6 Mile Rd"},
}

ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Compostables": "mdi:leaf",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address (e.g. '16795 Northville Rd')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

FEATURE_URL = "https://services.arcgis.com/eKu0BIfy09ymzWZF/arcgis/rest/services/Day_change_TrashCollection/FeatureServer/0"

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
}


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        address_upper = self._address.upper()

        try:
            features = query_feature_layer(
                FEATURE_URL,
                where=f"propstreetcombined LIKE '{address_upper}%'",
                out_fields="propstreetcombined,New_Day",
            )
        except ArcGisQueryError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        attrs = features[0]
        service_day = (attrs.get("New_Day") or "").strip()

        if not service_day or service_day not in WEEKDAYS:
            raise SourceArgumentNotFound("address", self._address)

        entries: list[Collection] = []
        for waste_type in ICON_MAP:
            entries.extend(self._weekly_dates(service_day, waste_type))

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
