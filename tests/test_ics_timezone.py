"""Regression tests for timezone handling in the shared ICS service.

icalevents normalises event start times to UTC. Reducing those straight to a
date silently shifts the collection day for feeds whose DTSTART is anchored at
midnight in a timezone other than UTC. The resulting date must depend only on
the timezone declared by the feed, never on the timezone the host happens to
run in.
"""

import datetime
import os
import sys

import pytest

sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    )
)

from waste_collection_schedule.service.ICS import ICS  # isort:skip

_HEAD = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//wcs-test//EN\n"
_TAIL = "END:VCALENDAR\n"

_WINDOWS_VTIMEZONE = (
    "BEGIN:VTIMEZONE\n"
    "TZID:AUS Eastern Standard Time\n"
    "BEGIN:STANDARD\n"
    "DTSTART:16010101T000000\n"
    "TZOFFSETFROM:+1000\n"
    "TZOFFSETTO:+1000\n"
    "END:STANDARD\n"
    "END:VTIMEZONE\n"
)


def _weekly_calendar(dtstart_line: str, vtimezone: str = "") -> str:
    """Build a calendar with a weekly recurring event starting on a Thursday."""
    return (
        _HEAD + vtimezone + "BEGIN:VEVENT\n"
        "UID:wcs-test\n"
        f"{dtstart_line}\n"
        "RRULE:FREQ=WEEKLY;BYDAY=TH\n"
        "SUMMARY:General waste\n"
        "END:VEVENT\n" + _TAIL
    )


# 2 Oct 2025 is a Thursday. Every occurrence of the weekly rule must land on a
# Thursday, whatever the feed's timezone and whatever the host's timezone.
CALENDARS = {
    "brisbane": _weekly_calendar(
        "DTSTART;TZID=Australia/Brisbane:20251002T000000"
    ),  # UTC+10
    "sydney": _weekly_calendar(
        "DTSTART;TZID=Australia/Sydney:20251002T000000"
    ),  # UTC+10/+11
    "auckland": _weekly_calendar(
        "DTSTART;TZID=Pacific/Auckland:20251002T000000"
    ),  # UTC+12/+13
    "berlin": _weekly_calendar(
        "DTSTART;TZID=Europe/Berlin:20251002T000000"
    ),  # UTC+1/+2
    "new_york": _weekly_calendar(
        "DTSTART;TZID=America/New_York:20251002T000000"
    ),  # UTC-5/-4
    "all_day": _weekly_calendar("DTSTART;VALUE=DATE:20251002"),
    "floating": _weekly_calendar("DTSTART:20251002T000000"),
    "utc": _weekly_calendar("DTSTART:20251002T060000Z"),
    "windows_tzid": _weekly_calendar(
        "DTSTART;TZID=AUS Eastern Standard Time:20251002T000000",
        vtimezone=_WINDOWS_VTIMEZONE,
    ),
}

# Home Assistant containers default to UTC; the others span both sides of UTC.
HOST_TIMEZONES = [
    "UTC",
    "Australia/Brisbane",
    "Europe/Berlin",
    "Pacific/Auckland",
    "America/Los_Angeles",
]


@pytest.fixture
def host_timezone(request, monkeypatch):
    """Pin the process-local timezone for the duration of a test."""
    import time

    monkeypatch.setenv("TZ", request.param)
    time.tzset()
    yield request.param
    monkeypatch.undo()
    time.tzset()


@pytest.mark.parametrize("host_timezone", HOST_TIMEZONES, indirect=True)
@pytest.mark.parametrize("name", sorted(CALENDARS))
def test_convert_keeps_the_calendar_day_of_the_feed(name, host_timezone) -> None:
    entries = ICS().convert(CALENDARS[name])

    assert entries, f"{name}: no entries returned"
    wrong = [d for d, _title in entries if d.weekday() != 3]  # 3 == Thursday
    assert not wrong, (
        f"{name}: {len(wrong)} of {len(entries)} entries shifted off Thursday "
        f"under TZ={host_timezone} (first bad date: {wrong[0]})"
    )


@pytest.mark.parametrize("host_timezone", HOST_TIMEZONES, indirect=True)
@pytest.mark.parametrize("name", sorted(CALENDARS))
def test_convert_events_agrees_with_convert(name, host_timezone) -> None:
    dates_convert = [d for d, _title in ICS().convert(CALENDARS[name])]
    dates_events = [event.date for event in ICS().convert_events(CALENDARS[name])]

    assert dates_convert == dates_events


def test_dst_transition_does_not_shift_the_day() -> None:
    """A feed anchored in summer time must stay correct once DST ends."""
    entries = ICS().convert(
        _weekly_calendar("DTSTART;TZID=Europe/Berlin:20250703T000000")
    )

    assert entries
    assert all(d.weekday() == 3 for d, _title in entries)


def test_all_day_events_keep_their_literal_date() -> None:
    """VALUE=DATE events carry no timezone and must never be converted."""
    entries = ICS().convert(
        _HEAD + "BEGIN:VEVENT\n"
        "UID:wcs-test-all-day\n"
        "DTSTART;VALUE=DATE:20251002\n"
        "DTEND;VALUE=DATE:20251003\n"
        "RRULE:FREQ=WEEKLY;BYDAY=TH\n"
        "SUMMARY:General waste\n"
        "END:VEVENT\n" + _TAIL
    )

    assert entries
    assert all(isinstance(d, datetime.date) for d, _title in entries)
    assert all(d.weekday() == 3 for d, _title in entries)
