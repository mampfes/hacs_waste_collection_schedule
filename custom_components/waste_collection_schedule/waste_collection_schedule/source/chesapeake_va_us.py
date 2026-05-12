from datetime import date, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Chesapeake, VA"
DESCRIPTION = "Source for Chesapeake, VA trash collection."
URL = "https://www.cityofchesapeake.net"
COUNTRY = "us"

TEST_CASES = {
    "460 Sawyers Mill Xing": {"address": "460 Sawyers Mill Xing, Chesapeake, VA 23323"},
}

ICON_MAP = {
    "Trash": "mdi:trash-can",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including city and state (e.g. '460 Sawyers Mill Xing, Chesapeake, VA 23323')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

MAPSERVER_URL = "https://gis.cityofchesapeake.net/mapping/rest/services/WasteManagement/Trash_Collection_Areas/MapServer/0"

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

        try:
            features = query_feature_layer(
                MAPSERVER_URL,
                geometry=location,
                out_fields="PICKUP_DAY",
            )
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        attrs = features[0]
        pickup_day = (attrs.get("PICKUP_DAY") or "").strip().title()

        if not pickup_day or pickup_day not in WEEKDAYS:
            raise SourceArgumentNotFound("address", self._address)

        return self._weekly_dates(pickup_day, "Trash")

    @staticmethod
    def _weekly_dates(day_name: str, waste_type: str) -> list[Collection]:
        weekday = WEEKDAYS[day_name]
        today = date.today()
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
