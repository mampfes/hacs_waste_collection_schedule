import re
from datetime import datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import ArcGisGeocodeError, geocode
from waste_collection_schedule.service.Pozi import PoziWfsError, query_wfs_layer

TITLE = "City of Vincent"
DESCRIPTION = "Source for City of Vincent (WA) waste collection."
URL = "https://www.vincent.wa.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "North Perth": {"address": "8 Kadina St, North Perth WA 6006"},
    "Leederville": {"address": "18 Stamford St, Leederville WA"},
    "Mount Lawley": {"address": "28 Ruby St, North Perth WA"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "FOGO": "mdi:leaf",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address within the City of Vincent (e.g. '8 Kadina St, North Perth WA 6006')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

WFS_BASE_URL = "https://mapping.vincent.wa.gov.au/pozi/qgisserver"
WFS_MAP_PATH = "C:/Pozi/Waste.qgs"
WFS_TYPENAME = "Waste_Collection"

# Matches: "15 Apr 2026 - Weekly (Wednesday)" or "15 Apr 2026 - Fortnightly (Thursday Week 2)"
# or "15 Apr 2026 - 2 x weekly (Wednesday/friday)"
_DATE_PATTERN = re.compile(
    r"(\d{1,2}\s+\w+\s+\d{4})\s*-\s*(.+?)\s*\((.+?)\)",
)

COLLECTION_FIELDS = {
    "General Waste Collection Day": "General Waste",
    "FOGO Collection Day": "FOGO",
    "Recycling Collection Day": "Recycling",
}


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisGeocodeError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        try:
            props = query_wfs_layer(
                WFS_BASE_URL,
                WFS_MAP_PATH,
                WFS_TYPENAME,
                lat=location["y"],
                lng=location["x"],
            )
        except PoziWfsError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        entries: list[Collection] = []

        for field, waste_type in COLLECTION_FIELDS.items():
            raw = props.get(field)
            if not raw:
                continue
            # Strip HTML tags
            text = re.sub(r"<[^>]+>", "", raw).strip()
            entries.extend(self._parse_collection(text, waste_type))

        return entries

    @staticmethod
    def _parse_collection(text: str, waste_type: str) -> list[Collection]:
        """Parse a collection day string into Collection objects.

        Expected formats (after stripping the label prefix):
            "15 Apr 2026 - Weekly (Wednesday)"
            "15 Apr 2026 - Fortnightly (Thursday Week 2)"
            "15 Apr 2026 - 2 x weekly (Wednesday/friday)"
        """
        # Remove the label prefix (e.g. "General Waste Collection Day:")
        if ":" in text:
            text = text.split(":", 1)[1].strip()

        match = _DATE_PATTERN.search(text)
        if not match:
            return []

        date_str, frequency, day_info = match.groups()
        frequency = frequency.strip().lower()

        try:
            next_date = datetime.strptime(date_str, "%d %b %Y").date()
        except ValueError:
            return []

        icon = ICON_MAP.get(waste_type)

        if "2 x weekly" in frequency or "2x weekly" in frequency:
            # Twice-weekly collection — parse both days
            return Source._twice_weekly_dates(day_info, waste_type, icon)
        elif "fortnightly" in frequency:
            return Source._fortnightly_dates(next_date, waste_type, icon)
        elif "weekly" in frequency:
            return Source._weekly_dates(next_date, waste_type, icon)

        return []

    @staticmethod
    def _weekly_dates(next_date, waste_type: str, icon: str | None) -> list[Collection]:
        return [
            Collection(
                date=next_date + timedelta(weeks=i),
                t=waste_type,
                icon=icon,
            )
            for i in range(26)
        ]

    @staticmethod
    def _fortnightly_dates(
        next_date, waste_type: str, icon: str | None
    ) -> list[Collection]:
        return [
            Collection(
                date=next_date + timedelta(days=i * 14),
                t=waste_type,
                icon=icon,
            )
            for i in range(13)
        ]

    @staticmethod
    def _twice_weekly_dates(
        day_info: str, waste_type: str, icon: str | None
    ) -> list[Collection]:
        """Generate dates for 2x weekly collection (e.g. 'Wednesday/friday')."""
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        days = [d.strip().lower() for d in day_info.split("/")]
        today = datetime.now().date()
        entries: list[Collection] = []

        for day_name in days:
            if day_name not in weekdays:
                continue
            weekday = weekdays[day_name]
            days_ahead = (weekday - today.weekday()) % 7
            next_date = today + timedelta(days=days_ahead)
            entries.extend(
                Collection(
                    date=next_date + timedelta(weeks=i),
                    t=waste_type,
                    icon=icon,
                )
                for i in range(26)
            )

        return entries
