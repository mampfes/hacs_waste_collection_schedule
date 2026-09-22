from datetime import date, timedelta

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Phoenix, AZ"
DESCRIPTION = "Source for City of Phoenix, AZ trash and recycling collection."
URL = "https://www.phoenix.gov/publicworks/garbage/trashschedule/find-your-day-of-collection"
COUNTRY = "us"

TEST_CASES = {
    "4750 S 48th St, Phoenix, AZ 85040": {
        "address": "4750 S 48th St, Phoenix, AZ 85040"
    },
    "With suite number": {"address": "4750 S 48th St SUITE 121, Phoenix, AZ 85040"},
}

ICON_MAP = {
    "Trash": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including city and state (e.g. '4750 S 48th St, Phoenix, AZ 85040')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

# City of Phoenix Public Works "GarbagePickUp" MapServer.
# Layer 2 = PW_GARBAGE (trash collection zones), layer 1 = PW_RECYCLE
# (recycling collection zones). Both layers expose a single "DOC"
# (day of collection) field, e.g. "FRIDAY".
MAPSERVER = "https://maps.phoenix.gov/pub/rest/services/Public/GarbagePickUp/MapServer"
GARBAGE_URL = f"{MAPSERVER}/2"
RECYCLE_URL = f"{MAPSERVER}/1"

WEEKDAYS = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}

WEEKS_AHEAD = 26


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        entries: list[Collection] = []

        garbage_day = self._query_day(location, GARBAGE_URL)
        if garbage_day is None:
            # No garbage zone means the address could not be matched at all.
            raise SourceArgumentNotFound("address", self._address)
        entries += self._weekly_dates(garbage_day, "Trash")

        # Not every address is eligible for city recycling service
        # (e.g. some multi-family or commercial buildings); skip if absent.
        recycle_day = self._query_day(location, RECYCLE_URL)
        if recycle_day is not None:
            entries += self._weekly_dates(recycle_day, "Recycling")

        return entries

    @staticmethod
    def _query_day(location: dict[str, float], url: str) -> str | None:
        try:
            features = query_feature_layer(url, geometry=location, out_fields="DOC")
        except ArcGisError:
            return None

        value = (features[0].get("DOC") or "").strip().upper()
        if value not in WEEKDAYS:
            return None
        return value

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
            for i in range(WEEKS_AHEAD)
        ]
