import re
from datetime import date, timedelta

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    geocode,
    query_feature_layer,
)

TITLE = "Abilene, TX"
DESCRIPTION = "Source for Abilene, TX solid waste and yard waste collection."
URL = "https://abilenetx.gov/426/Solid-Waste-Recycling"
COUNTRY = "us"

TEST_CASES = {
    "Chimney Rock Rd (Mon/Thu trash, 4th-Monday yard)": {
        "address": "3601 Chimney Rock Rd, Abilene, TX"
    },
    "City Hall area (Tue/Fri trash)": {"address": "555 Walnut St, Abilene, TX"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including city and state (e.g. '3601 Chimney Rock Rd, Abilene, TX')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

TRASH_URL = "https://services6.arcgis.com/iBFmWI3dYPQqS1KF/arcgis/rest/services/Trash_Pickup/FeatureServer/0"
YARD_WASTE_URL = "https://services6.arcgis.com/iBFmWI3dYPQqS1KF/arcgis/rest/services/Yard_Waste_Pickup/FeatureServer/0"

ICON_MAP = {
    "Trash": Icons.GENERAL_WASTE,
    "Yard Waste": Icons.GARDEN,
}

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

WEEKS_AHEAD = 26


def _weekly_dates(day_name: str, waste_type: str) -> list[Collection]:
    """Generate ~26 weeks of Collection entries for a given weekday."""
    weekday_idx = WEEKDAYS.get(day_name.lower())
    if weekday_idx is None:
        return []
    today = date.today()
    days_ahead = (weekday_idx - today.weekday()) % 7
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


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Return the nth occurrence (1-based) of weekday (0=Mon) in the given month/year."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    first_occurrence = first + timedelta(days=offset)
    return first_occurrence + timedelta(weeks=n - 1)


def _parse_yard_waste(pickup_time: str) -> list[Collection]:
    """Parse 'Nth DAY | ... | Odd/Even Months' into Collection dates."""
    match = re.match(
        r"(\d+)(?:st|nd|rd|th)\s+(\w+)\s*\|.*?(Odd|Even)\s+Months",
        pickup_time,
        re.IGNORECASE,
    )
    if not match:
        return []

    n = int(match.group(1))
    day_name = match.group(2).lower()
    parity = match.group(3).lower()

    weekday_idx = WEEKDAYS.get(day_name)
    if weekday_idx is None:
        return []

    today = date.today()
    icon = ICON_MAP.get("Yard Waste")
    entries: list[Collection] = []

    for year in range(today.year, today.year + 2):
        for month in range(1, 13):
            month_is_odd = month % 2 == 1
            if parity == "odd" and not month_is_odd:
                continue
            if parity == "even" and month_is_odd:
                continue
            try:
                d = _nth_weekday_of_month(year, month, weekday_idx, n)
            except ValueError:
                continue
            if d >= today:
                entries.append(
                    Collection(
                        date=d,
                        t="Yard Waste",
                        icon=icon,
                    )
                )

    return entries


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        entries: list[Collection] = []

        try:
            features = query_feature_layer(
                TRASH_URL, geometry=location, out_fields="Name"
            )
            name = (features[0].get("Name") or "").strip()
            for day in name.split("/"):
                entries.extend(_weekly_dates(day.strip(), "Trash"))
        except ArcGisError:
            pass

        try:
            features = query_feature_layer(
                YARD_WASTE_URL, geometry=location, out_fields="Pickup_Time"
            )
            pickup_time = (features[0].get("Pickup_Time") or "").strip()
            entries.extend(_parse_yard_waste(pickup_time))
        except ArcGisError:
            pass

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

        return entries
