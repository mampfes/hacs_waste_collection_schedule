import re
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import ArcGisGeocodeError, geocode
from waste_collection_schedule.service.Pozi import (
    PoziError,
    PoziWfsError,
    query_wfs_layer,
)

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
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "FOGO": Icons.BIO_KITCHEN,
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

# The council's own mapping host still advertises the Waste_Collection layer but
# serves no features for it. Its Pozi viewer reads the same QGIS project through
# the tenant's dataset proxy, so look the dataset up there instead of hard-coding
# an id that changes whenever the council republishes the project.
DATASETS_API_URL = "https://vincent.pozi.com/api/v1/public/maps/waste/datasets"
QGIS_PROJECT_DATASET_TYPE = 1
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


def _waste_dataset_url() -> str:
    """Return the WFS endpoint of the council's waste QGIS project."""
    r = requests.get(DATASETS_API_URL, timeout=30)
    r.raise_for_status()

    for group in r.json().get("mapdatasets", []):
        for dataset in group.get("datasets", []):
            if dataset.get("type") == QGIS_PROJECT_DATASET_TYPE and dataset.get("url"):
                return dataset["url"]

    raise PoziError(f"No QGIS project dataset advertised at {DATASETS_API_URL}")


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisGeocodeError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        # not inside the try below: a missing dataset is not a bad address
        dataset_url = _waste_dataset_url()

        try:
            props = query_wfs_layer(
                dataset_url,
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
        if "fortnightly" in frequency:
            return Source._fortnightly_dates(next_date, waste_type, icon)
        if "weekly" in frequency:
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
