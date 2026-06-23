from datetime import date, timedelta

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    epoch_ms_to_date,
    geocode,
    query_feature_layer,
)

TITLE = "Alexandria, VA"
DESCRIPTION = "Source for City of Alexandria, VA trash, recycling and leaf collection."
URL = "https://www.alexandriava.gov/RefuseCollection"
COUNTRY = "us"

TEST_CASES = {
    "City Hall, 301 King St": {"address": "301 King St, Alexandria, VA 22314"},
}

SOURCE_CODEOWNERS = ["@lpukatch"]

ICON_MAP = {
    "Trash": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Leaf Collection": Icons.ORGANIC,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including city and state (e.g. '301 King St, Alexandria, VA 22314')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

# City of Alexandria alx311Info MapServer.
# Layer 3 = Refuse Day Zone (field DAYSERVED), layer 2 = Recycle Zones (field PICKUPDAY),
# layer 16 = Leaf Zones (field PassDate, one feature per seasonal collection pass).
MAPSERVER = "https://maps.alexandriava.gov/alexmaps/rest/services/alx311Info/MapServer"
REFUSE_URL = f"{MAPSERVER}/3"
RECYCLE_URL = f"{MAPSERVER}/2"
LEAF_URL = f"{MAPSERVER}/16"

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
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

        # Trash / refuse — every eligible address falls in a refuse day zone.
        refuse_day = self._query_day(location, REFUSE_URL, "DAYSERVED")
        if refuse_day is None:
            # No refuse zone means the address could not be matched at all.
            raise SourceArgumentNotFound("address", self._address)
        entries += self._weekly_dates(refuse_day, "Trash")

        # Recycling — not every address is eligible for city recycling
        # (e.g. commercial buildings return PICKUPDAY "None"); skip if absent.
        recycle_day = self._query_day(location, RECYCLE_URL, "PICKUPDAY")
        if recycle_day is not None:
            entries += self._weekly_dates(recycle_day, "Recycling")

        # Leaf collection — seasonal vacuum-leaf passes with explicit dates.
        # The layer only holds the current season, so this yields nothing
        # outside the fall/winter leaf-collection period.
        entries += self._leaf_dates(location)

        return entries

    @staticmethod
    def _query_day(location: dict[str, float], url: str, field: str) -> str | None:
        try:
            features = query_feature_layer(url, geometry=location, out_fields=field)
        except ArcGisError:
            return None

        value = (features[0].get(field) or "").strip().title()
        if value not in WEEKDAYS:
            return None
        return value

    @staticmethod
    def _leaf_dates(location: dict[str, float]) -> list[Collection]:
        try:
            features = query_feature_layer(
                LEAF_URL, geometry=location, out_fields="PassDate"
            )
        except ArcGisError:
            return []

        icon = ICON_MAP.get("Leaf Collection")
        entries: list[Collection] = []
        for attrs in features:
            pass_date = attrs.get("PassDate")
            if not pass_date:
                continue
            entries.append(
                Collection(
                    date=epoch_ms_to_date(pass_date),
                    t="Leaf Collection",
                    icon=icon,
                )
            )
        return entries

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
