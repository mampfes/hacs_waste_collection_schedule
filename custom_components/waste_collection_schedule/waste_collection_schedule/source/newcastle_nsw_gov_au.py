from datetime import date, datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "City of Newcastle"
DESCRIPTION = "Source for City of Newcastle (NSW) waste collection."
URL = "https://www.newcastle.nsw.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "King Street": {"address": "1 King Street, Newcastle NSW 2300"},
    "Stockton": {"address": "5 Pacific Street, Stockton NSW 2295"},
    "Waratah": {"address": "30 Turton Road, Waratah NSW 2298"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address within the City of Newcastle (e.g. '1 King Street, Newcastle NSW 2300')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

FEATURE_URL = "https://services-ap1.arcgis.com/CNeUPE1voVc22gNk/arcgis/rest/services/WasteCollectionDay/FeatureServer/0"

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
}

# Reference date for the fortnightly cycle, from the ArcGIS Arcade expression
# in the web app. June 28, 2021 is week 0, which maps to CalWk=2 (even).
# So Week 1 starts July 5, 2021.
EPOCH = date(2021, 6, 28)


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
            features = query_feature_layer(
                FEATURE_URL,
                geometry=location,
                out_fields="WeekNo,Day",
            )
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        attrs = features[0]
        day = attrs.get("Day", "").strip()
        week_no = attrs.get("WeekNo")

        if not day or day not in WEEKDAYS or week_no not in (1, 2):
            raise SourceArgumentNotFound("address", self._address)

        entries: list[Collection] = []

        # General Waste (RED lid) — weekly
        entries.extend(self._weekly_dates(day, "General Waste"))

        # Recycling (YELLOW lid) — fortnightly, on weeks matching WeekNo
        recycling_base = self._base_date_for_week(day, week_no)
        entries.extend(self._fortnightly_dates(recycling_base, "Recycling"))

        # Green Waste (GREEN lid) — fortnightly, on the opposite week
        green_base = recycling_base + timedelta(days=7)
        entries.extend(self._fortnightly_dates(green_base, "Green Waste"))

        return entries

    @staticmethod
    def _base_date_for_week(day: str, week_no: int) -> date:
        """Find a reference date for the given day that falls on a matching week.

        The Arcade expression defines:
        - week_index = floor(days_since_epoch / 7)
        - CalWk = 2 if week_index is even, else 1
        So EPOCH (June 28, 2021) is CalWk=2 (week_index=0, even).
        """
        weekday = WEEKDAYS[day]
        # Start from EPOCH and find the first occurrence of the target weekday
        days_offset = (weekday - EPOCH.weekday()) % 7
        candidate = EPOCH + timedelta(days=days_offset)

        # Check which CalWk this candidate falls in
        week_index = (candidate - EPOCH).days // 7
        cal_wk = 2 if week_index % 2 == 0 else 1

        # If it doesn't match, shift by one week
        if cal_wk != week_no:
            candidate += timedelta(days=7)

        return candidate

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
