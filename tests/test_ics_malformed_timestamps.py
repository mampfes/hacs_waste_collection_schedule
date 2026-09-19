"""Regression tests for malformed timestamp properties in the shared ICS service.

Some generators append a second time component to their UTC timestamp
properties, e.g. "CREATED:20260101T000000ZT000000Z". Current icalendar versions
refuse to parse such a value, and icalevents raises as soon as the property is
accessed, so every fetch of an affected feed failed. The service drops the
duplicated suffix before parsing; well-formed feeds must be left untouched.
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

# The service only returns events from today onwards, so anchor on a future day.
EVENT_DAY = datetime.date.today() + datetime.timedelta(days=30)


def _calendar(created: str, newline: str = "\r\n") -> str:
    return newline.join(
        [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//wcs-test//EN",
            "BEGIN:VEVENT",
            "UID:wcs-test",
            f"CREATED:{created}",
            f"DTSTAMP:{created}",
            f"LAST-MODIFIED:{created}",
            f"DTSTART;VALUE=DATE:{EVENT_DAY:%Y%m%d}",
            f"DTEND;VALUE=DATE:{EVENT_DAY + datetime.timedelta(days=1):%Y%m%d}",
            "SUMMARY:Gelber-Sack",
            "END:VEVENT",
            "END:VCALENDAR",
            "",
        ]
    )


MALFORMED = "20260101T000000ZT000000Z"
WELL_FORMED = "20260101T000000Z"


@pytest.mark.parametrize("newline", ["\r\n", "\n"], ids=["crlf", "lf"])
def test_duplicated_time_suffix_is_dropped(newline: str) -> None:
    """A feed with a doubled time component still yields its collections."""
    assert ICS().convert(_calendar(MALFORMED, newline)) == [(EVENT_DAY, "Gelber-Sack")]


@pytest.mark.parametrize("newline", ["\r\n", "\n"], ids=["crlf", "lf"])
def test_convert_events_agrees_with_convert(newline: str) -> None:
    events = ICS().convert_events(_calendar(MALFORMED, newline))
    assert [(e.date, e.title) for e in events] == [(EVENT_DAY, "Gelber-Sack")]


def test_well_formed_timestamps_are_untouched() -> None:
    """The sanitiser must not alter a conforming feed."""
    assert ICS().convert(_calendar(WELL_FORMED)) == [(EVENT_DAY, "Gelber-Sack")]
