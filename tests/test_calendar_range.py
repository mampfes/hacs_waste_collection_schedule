"""Regression tests for the time range of WasteCollectionCalendar.async_get_events.

Home Assistant asks a calendar for the events that overlap [start, end): the
end is exclusive. Collections are all-day events, so a collection on the day
that starts exactly at ``end`` must not be returned. Otherwise an automation
that asks for "tomorrow" (midnight to midnight) also gets the day after.
Today's collection must still be returned when the range starts after
midnight (#5852).
"""

import asyncio
import os
import sys
from datetime import date, datetime
from unittest.mock import Mock

import homeassistant.util.dt as dt_util
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))  # isort:skip
from custom_components.waste_collection_schedule.calendar import (  # isort:skip
    WasteCollectionCalendar,
)
from custom_components.waste_collection_schedule.waste_collection_schedule import (  # isort:skip
    Collection,
)

TZ = "Europe/Rome"

COLLECTIONS = [
    Collection(date(2026, 11, 4), "Paper"),
    Collection(date(2026, 11, 5), "Organic"),
    Collection(date(2026, 11, 5), "Glass"),
    Collection(date(2026, 11, 6), "Residual"),
]


@pytest.fixture(autouse=True)
def local_time_zone():
    previous = dt_util.DEFAULT_TIME_ZONE
    dt_util.set_default_time_zone(dt_util.get_time_zone(TZ))
    yield
    dt_util.set_default_time_zone(previous)


def _local(day: int, hour: int = 0, minute: int = 0) -> datetime:
    """A wall-clock time in November 2026, local time."""
    return datetime(2026, 11, day, hour, minute, tzinfo=dt_util.get_time_zone(TZ))


def _events(start: datetime, end: datetime) -> list[tuple[date, str]]:
    aggregator = Mock()
    aggregator.get_upcoming.return_value = COLLECTIONS
    calendar = WasteCollectionCalendar(
        aggregator=aggregator, name="Test", unique_id="test_calendar"
    )
    events = asyncio.run(calendar.async_get_events(Mock(), start, end))
    return [(event.start, event.summary) for event in events]


def test_end_is_exclusive():
    # "Tomorrow" from midnight to midnight: the day after is not part of it.
    assert _events(_local(5), _local(6)) == [
        (date(2026, 11, 5), "Organic"),
        (date(2026, 11, 5), "Glass"),
    ]


def test_day_before_start_is_excluded():
    assert _events(_local(5), _local(7)) == [
        (date(2026, 11, 5), "Organic"),
        (date(2026, 11, 5), "Glass"),
        (date(2026, 11, 6), "Residual"),
    ]


def test_today_is_kept_when_range_starts_after_midnight():
    # The frontend asks from "now", e.g. 05:30, not from midnight (#5852).
    assert _events(_local(5, 5, 30), _local(5, 23, 0)) == [
        (date(2026, 11, 5), "Organic"),
        (date(2026, 11, 5), "Glass"),
    ]


def test_range_in_another_time_zone():
    # The same instants written in UTC: 2026-11-04T23:00Z is local midnight.
    utc = dt_util.UTC
    assert _events(
        datetime(2026, 11, 4, 23, 0, tzinfo=utc),
        datetime(2026, 11, 5, 23, 0, tzinfo=utc),
    ) == [
        (date(2026, 11, 5), "Organic"),
        (date(2026, 11, 5), "Glass"),
    ]
