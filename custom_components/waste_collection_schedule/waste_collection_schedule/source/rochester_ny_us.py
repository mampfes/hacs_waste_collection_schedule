import re
from datetime import datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Rochester, NY"
DESCRIPTION = "Source for Rochester, NY waste collection."
URL = "https://www.cityofrochester.gov"
COUNTRY = "us"

TEST_CASES = {
    "Parsells Ave (Wed/A)": {"address": "124 Parsells Ave, Rochester, NY"},
    "Lyell Ave (Mon/B)": {"address": "200 Lyell Ave, Rochester, NY"},
}

ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address (e.g. '124 Parsells Ave, Rochester, NY')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

BASE_URL = "http://maps.cityofrochester.gov/arcgis/rest/services/App_CityServices/City_Services/MapServer"
TRASH_URL = f"{BASE_URL}/8"
RECYCLING_URL = f"{BASE_URL}/9"

DAY_FIELDS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
}

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

# Regex to extract month and day from NEXTPICKUP/TRASHPICKUPIS fields
# e.g. "in two weeks on Wednesday, April 22</a>"
DATE_RE = re.compile(r"(?P<month>" + "|".join(MONTHS.keys()) + r")\s+(?P<day>\d{1,2})")


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        entries: list[Collection] = []

        # Trash pickup — weekly
        try:
            trash_features = query_feature_layer(
                TRASH_URL,
                geometry=location,
                out_fields=",".join(DAY_FIELDS),
            )
            trash_day = self._get_collection_day(trash_features[0])
            if trash_day:
                entries.extend(self._weekly_dates(trash_day, "Trash"))
        except ArcGisError:
            pass

        # Recycling pickup — bi-weekly
        try:
            recycling_features = query_feature_layer(
                RECYCLING_URL,
                geometry=location,
                out_fields="NEXTPICKUP,DOW," + ",".join(DAY_FIELDS),
            )
            attrs = recycling_features[0]
            recycling_base = self._parse_next_date(attrs.get("NEXTPICKUP", ""))
            if recycling_base:
                entries.extend(self._fortnightly_dates(recycling_base, "Recycling"))
            else:
                # Fallback: use DOW or day fields for weekly recycling
                day = attrs.get("DOW", "").strip()
                if not day:
                    day = self._get_collection_day(attrs)
                if day:
                    entries.extend(self._weekly_dates(day, "Recycling"))
        except ArcGisError:
            pass

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

        return entries

    @staticmethod
    def _get_collection_day(attrs: dict) -> str | None:
        # ArcGIS may return field names in varying case (MONDAY vs Monday)
        attrs_upper = {k.upper(): v for k, v in attrs.items()}
        for day in DAY_FIELDS:
            if (attrs_upper.get(day.upper()) or "").strip().lower() == "yes":
                return day
        return None

    @staticmethod
    def _parse_next_date(text: str) -> datetime | None:
        if not text:
            return None
        match = DATE_RE.search(text)
        if not match:
            return None
        month = MONTHS[match.group("month")]
        day = int(match.group("day"))
        today = datetime.now().date()
        # Assume current year, but if the date is far in the past, use next year
        year = today.year
        try:
            result = datetime(year, month, day).date()
        except ValueError:
            return None
        if result < today - timedelta(days=60):
            result = datetime(year + 1, month, day).date()
        return result

    @staticmethod
    def _weekly_dates(day_name: str, waste_type: str) -> list[Collection]:
        weekday = WEEKDAYS.get(day_name)
        if weekday is None:
            return []
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
    def _fortnightly_dates(base_date, waste_type: str) -> list[Collection]:
        icon = ICON_MAP.get(waste_type)
        return [
            Collection(
                date=base_date + timedelta(days=i * 14),
                t=waste_type,
                icon=icon,
            )
            for i in range(13)
        ]
