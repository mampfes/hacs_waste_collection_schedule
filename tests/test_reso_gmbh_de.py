"""Tests for the reso_gmbh_de feed handling.

The RESO feed appends a second time to its timestamps
("CREATED:20260101T000000ZT000000Z"). Newer icalendar versions refuse to parse
those values, so every fetch raised. The source now drops the duplicated suffix
before handing the feed to the ICS parser.
"""

import os
import sys
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
            "waste_collection_schedule",
        )
    )
)

from waste_collection_schedule.source.reso_gmbh_de import Source

# The ICS parser only returns upcoming events, so build the date relative to today.
EVENT_DAY = date.today() + timedelta(days=30)

ICS_TEXT = "\r\n".join(
    [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//test//iCal//DE",
        "BEGIN:VEVENT",
        "CREATED:20260101T000000ZT000000Z",
        f"DTSTART;VALUE=DATE:{EVENT_DAY:%Y%m%d}",
        f"DTEND;VALUE=DATE:{EVENT_DAY + timedelta(days=1):%Y%m%d}",
        "LAST-MODIFIED:20260101T000000ZT000000Z",
        "SUMMARY:Gelber-Sack",
        "UID:reso-test-1",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
)


def test_feed_with_duplicated_timestamp_suffix_is_parsed():
    response = MagicMock(text=ICS_TEXT)
    with patch("requests.post", return_value=response):
        entries = Source(ort="Reichelsheim", ortsteil="Kerngemeinde").get_data(2026)
    assert [(e.date, e.type) for e in entries] == [(EVENT_DAY, "Gelber-Sack")]
