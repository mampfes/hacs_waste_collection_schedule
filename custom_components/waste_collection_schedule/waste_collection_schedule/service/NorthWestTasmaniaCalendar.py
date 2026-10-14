"""Parse published NWRRR calendar properties using shared recurrence helpers."""

import logging
from datetime import date, timedelta
from typing import Any

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser

_LOGGER = logging.getLogger(__name__)
GEOJSON_URL = "https://nwrrr.eskspatial.com.au/assets/all_councils.geojson"
LOOKAHEAD_DAYS = 365


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
        return recurrence.next_weekday(anchor.weekday(), on_or_after=from_date)
    if frequency == "bi-weekly":
        candidate = recurrence.next_weekday(anchor.weekday(), on_or_after=from_date)
        diff = (candidate - anchor).days
        if diff % 14 == 0:
            return candidate
        return candidate + timedelta(days=7)
    if frequency == "monthly":
        weekday = anchor.weekday()
        nth = (anchor.day - 1) // 7
        return _nth_weekday_of_month(from_date, weekday, nth)
    _LOGGER.warning("Unknown frequency %r — skipping", frequency)
    return None


def _nth_weekday_of_month(from_date: date, weekday: int, nth: int) -> date:
    """Return the (nth+1)-th occurrence of *weekday* in the current month,
    or the same occurrence in the following month if that date has passed."""
    first = from_date.replace(day=1)
    candidate = recurrence.next_weekday(weekday, on_or_after=first) + timedelta(
        weeks=nth
    )
    if candidate >= from_date:
        return candidate
    if first.month == 12:
        next_first = first.replace(year=first.year + 1, month=1)
    else:
        next_first = first.replace(month=first.month + 1)
    return recurrence.next_weekday(weekday, on_or_after=next_first) + timedelta(
        weeks=nth
    )


class _CalendarClient:
    def __init__(self, municipality: str, region: str):
        self._municipality = municipality.strip()
        self._region = region.strip()

    def parse(self, r):
        features = r.json().get("features", [])
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
                    "region", self._region, available_regions
                )
            available_municipalities = sorted(
                {
                    f["properties"]["municipality"]
                    for f in features
                    if f.get("properties", {}).get("municipality")
                }
            )
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, available_municipalities
            )
        return self._build_collections(properties)

    def _build_collections(self, p: dict) -> list[dict]:
        today = date.today()
        end = today + timedelta(days=LOOKAHEAD_DAYS)
        entries: list[dict] = []
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
            current = today
            while True:
                next_date = _next_collection(current, anchor, frequency)
                if next_date is None or next_date > end:
                    break
                entries.append({"date": next_date, "type": waste_type})
                current = next_date + timedelta(days=1)
        return entries


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        response.raise_for_status()
        return client.parse(response)
