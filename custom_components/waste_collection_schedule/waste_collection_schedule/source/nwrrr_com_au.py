import logging
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "North West Resource Recovery and Recycling"
DESCRIPTION = "Source for North West Resource Recovery and Recycling (NWRRR), serving 8 councils in north-west Tasmania, Australia."
URL = "https://www.nwrrr.com.au"
COUNTRY = "au"

TEST_CASES = {
    "Devonport (Thursday)": {
        "municipality": "Devonport",
        "region": "Devonport (Thursday)",
    },
    "Strahan (West Coast)": {
        "municipality": "West Coast",
        "region": "Strahan",
    },
    "Smithton East (Circular Head)": {
        "municipality": "Circular Head",
        "region": "Smithton East",
    },
    "Hawley/Shearwater (Latrobe)": {
        "municipality": "Latrobe",
        "region": "Hawley/Shearwater",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://www.nwrrr.com.au/map, click 'Select Location', then choose your council and region from the list. Use the displayed council name as 'municipality' and the region name as 'region'.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": "Council name (e.g. 'Devonport', 'Burnie', 'Central Coast', 'Circular Head', 'Kentish', 'Latrobe', 'Waratah Wynyard', 'West Coast')",
        "region": "Region name within the council (e.g. 'Devonport (Thursday)', 'Smithton East', 'Ulverstone')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "municipality": "Municipality / Council",
        "region": "Region",
    },
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "FOGO": Icons.ORGANIC,
}

GEOJSON_URL = "https://nwrrr.eskspatial.com.au/assets/all_councils.geojson"
LOOKAHEAD_DAYS = 365


class Source:
    def __init__(self, municipality: str, region: str):
        self._municipality = municipality.strip()
        self._region = region.strip()

    def fetch(self) -> list[Collection]:
        r = requests.get(GEOJSON_URL, timeout=30)
        r.raise_for_status()

        features = r.json().get("features", [])

        # Find the matching feature (first match wins; duplicates share identical schedules)
        properties = None
        for feat in features:
            p = feat.get("properties", {})
            if (
                p.get("municipality", "").strip().lower() == self._municipality.lower()
                and p.get("region_name", "").strip().lower() == self._region.lower()
            ):
                properties = p
                break

        if properties is None:
            # Build suggestions for SourceArgumentNotFoundWithSuggestions
            available_regions = sorted(
                {
                    f["properties"]["region_name"]
                    for f in features
                    if f.get("properties", {}).get("municipality", "").strip().lower()
                    == self._municipality.lower()
                }
            )
            if available_regions:
                raise SourceArgumentNotFoundWithSuggestions(
                    "region",
                    self._region,
                    available_regions,
                )
            available_municipalities = sorted(
                {
                    f["properties"]["municipality"]
                    for f in features
                    if f.get("properties", {}).get("municipality")
                }
            )
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality",
                self._municipality,
                available_municipalities,
            )

        return self._build_collections(properties)

    def _build_collections(self, p: dict) -> list[Collection]:
        today = date.today()
        end = today + timedelta(days=LOOKAHEAD_DAYS)
        entries: list[Collection] = []

        schedule = [
            ("General Waste", p.get("landfill_date"), p.get("landfill_freq")),
            ("Recycling", p.get("recycling_date"), p.get("recycling_freq")),
            ("FOGO", p.get("fogo_date"), p.get("fogo_freq")),
        ]

        for waste_type, anchor_str, frequency in schedule:
            if not anchor_str or not frequency:
                continue
            try:
                anchor = date.fromisoformat(anchor_str)
            except ValueError:
                _LOGGER.warning(
                    "Could not parse anchor date %r for %s", anchor_str, waste_type
                )
                continue

            icon = ICON_MAP.get(waste_type)
            current = today
            while True:
                next_date = _next_collection(current, anchor, frequency)
                if next_date is None or next_date > end:
                    break
                entries.append(Collection(date=next_date, t=waste_type, icon=icon))
                current = next_date + timedelta(days=1)

        return entries


def _next_collection(from_date: date, anchor: date, frequency: str) -> date | None:
    """Return the next collection date on or after *from_date*.

    Uses the same algorithm as the nwrrr.eskspatial.com.au Angular app:

    - **weekly**: next occurrence of the anchor's weekday.
    - **bi-weekly**: next occurrence of the anchor's weekday that falls on an
      even number of weeks from the anchor date (i.e. ``(candidate - anchor).days
      % 14 == 0``).
    - **monthly**: same ordinal weekday of the month (e.g. 2nd Friday).
    """
    if frequency == "weekly":
        return _next_weekday(from_date, anchor.weekday())

    if frequency == "bi-weekly":
        candidate = _next_weekday(from_date, anchor.weekday())
        diff = (candidate - anchor).days
        if diff % 14 == 0:
            return candidate
        # Off-week — advance one more week
        return candidate + timedelta(days=7)

    if frequency == "monthly":
        weekday = anchor.weekday()
        nth = (anchor.day - 1) // 7  # 0-indexed ordinal (0 = 1st, 1 = 2nd, …)
        return _nth_weekday_of_month(from_date, weekday, nth)

    _LOGGER.warning("Unknown frequency %r — skipping", frequency)
    return None


def _next_weekday(from_date: date, weekday: int) -> date:
    """Return the first date >= *from_date* that falls on *weekday* (0=Mon)."""
    days_ahead = (weekday - from_date.weekday()) % 7
    return from_date + timedelta(days=days_ahead)


def _nth_weekday_of_month(from_date: date, weekday: int, nth: int) -> date:
    """Return the (nth+1)-th occurrence of *weekday* in the current month,
    or the same occurrence in the following month if that date has passed."""
    first = from_date.replace(day=1)
    days_to_first = (weekday - first.weekday()) % 7
    candidate = first + timedelta(days=days_to_first + 7 * nth)
    if candidate >= from_date:
        return candidate
    # Move to next month
    if first.month == 12:
        next_first = first.replace(year=first.year + 1, month=1)
    else:
        next_first = first.replace(month=first.month + 1)
    days_to_first = (weekday - next_first.weekday()) % 7
    return next_first + timedelta(days=days_to_first + 7 * nth)
