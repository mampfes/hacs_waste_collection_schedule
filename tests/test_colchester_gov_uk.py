"""
Unit tests for Colchester City Council waste collection source.

Note: This test file is not auto-discovered by pytest due to pytest.ini configuration
(python_files = test_source_components.py). Run it explicitly:

    pytest tests/test_colchester_gov_uk.py
    pytest tests/test_colchester_gov_uk.py -v
"""

import json
import os
import sys
from datetime import date as real_date
from datetime import datetime
from unittest.mock import patch

import pytest

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

from waste_collection_schedule import Icons
from waste_collection_schedule.source import colchester_gov_uk


class MockResponse:
    """Minimal requests.Response stand-in (the source reads .text)."""

    def __init__(self, payload):
        self.text = json.dumps(payload)
        self.status_code = 200


class FrozenDatetime(datetime):
    """Subclass datetime so .now() is deterministic but .strptime() still works."""

    _now = datetime(2026, 5, 25, 12, 0, 0)

    @classmethod
    def now(cls, tz=None):
        return cls._now


# A Tuesday before the first collection in the sample (2026-05-26), so the
# initial-week entries are always in the future.
FROZEN_NOW = datetime(2026, 5, 25, 12, 0, 0)


def _payload(
    week_one_names, week_two_names, day="Tuesday", first_date="2026-05-26T00:00:00"
):
    """Build a minimal calendar payload in the new (post-2026-06) feed shape."""
    return {
        "Weeks": [
            {
                "Rows": {
                    day: [
                        {"Name": n, "ReportableBecauseWeeklyExemption": False}
                        for n in week_one_names
                    ]
                },
                "WeekOne": True,
            },
            {
                "Rows": {
                    day: [
                        {"Name": n, "ReportableBecauseWeeklyExemption": False}
                        for n in week_two_names
                    ]
                },
                "WeekOne": False,
            },
        ],
        "DatesOfFirstCollectionDays": {day: first_date},
        "Today": "2026-05-25T12:00:00",
        "AddressName": "Test Address",
        "PostCode": "CO1 1AA",
    }


# ---------------------------------------------------------------------------
# Current (post-rename) feed: waste-type names must round-trip with correct icons
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "feed_name,expected_name,expected_icon",
    [
        # The two newly-renamed waste types must round-trip in sentence case
        # so the label stays consistent with the previous fix's "Mixed recycling".
        ("Non-recyclable rubbish", "Non-recyclable rubbish", Icons.GENERAL_WASTE),
        ("Mixed recycling", "Mixed recycling", Icons.RECYCLING),
        # Unchanged categories: existing .title() behaviour is preserved.
        ("Glass", "Glass", Icons.GLASS),
        ("Food waste", "Food Waste", Icons.BIO_KITCHEN),
        ("Garden waste", "Garden Waste", Icons.GARDEN),
    ],
)
@patch("waste_collection_schedule.source.colchester_gov_uk.datetime", FrozenDatetime)
@patch("waste_collection_schedule.source.colchester_gov_uk.requests")
def test_new_feed_name_and_icon(mock_requests, feed_name, expected_name, expected_icon):
    mock_requests.get.return_value = MockResponse(_payload([feed_name], []))
    entries = colchester_gov_uk.Source(llpgid="test").fetch()
    assert entries, f"Expected at least one Collection for {feed_name!r}"
    for e in entries:
        assert e.type == expected_name, f"Name {e.type!r} != {expected_name!r}"
        assert e.icon == expected_icon, f"Icon {e.icon!r} != {expected_icon!r}"


# ---------------------------------------------------------------------------
# Legacy (pre-rename) feed: defensive mapping during the provider's rollout
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "legacy_name,expected_name,expected_icon",
    [
        ("Black bags", "Non-recyclable rubbish", Icons.GENERAL_WASTE),
        ("Paper/card", "Mixed recycling", Icons.RECYCLING),
    ],
)
@patch("waste_collection_schedule.source.colchester_gov_uk.datetime", FrozenDatetime)
@patch("waste_collection_schedule.source.colchester_gov_uk.requests")
def test_legacy_feed_name_and_icon(
    mock_requests, legacy_name, expected_name, expected_icon
):
    mock_requests.get.return_value = MockResponse(_payload([legacy_name], []))
    entries = colchester_gov_uk.Source(llpgid="test").fetch()
    assert entries, f"Expected at least one Collection for legacy {legacy_name!r}"
    for e in entries:
        assert e.type == expected_name
        assert e.icon == expected_icon


# ---------------------------------------------------------------------------
# Integration: the exact response shape reported by the live API on 2026-05-29
# ---------------------------------------------------------------------------


@patch("waste_collection_schedule.source.colchester_gov_uk.datetime", FrozenDatetime)
@patch("waste_collection_schedule.source.colchester_gov_uk.requests")
def test_full_response_produces_expected_collections(mock_requests):
    payload = {
        "Weeks": [
            {
                "Rows": {
                    "Tuesday": [
                        {
                            "Name": "Non-recyclable rubbish",
                            "ReportableBecauseWeeklyExemption": False,
                        },
                        {
                            "Name": "Food waste",
                            "ReportableBecauseWeeklyExemption": False,
                        },
                    ]
                },
                "WeekOne": True,
            },
            {
                "Rows": {
                    "Tuesday": [
                        {"Name": "Glass", "ReportableBecauseWeeklyExemption": False},
                        {
                            "Name": "Mixed recycling",
                            "ReportableBecauseWeeklyExemption": False,
                        },
                        {
                            "Name": "Food waste",
                            "ReportableBecauseWeeklyExemption": False,
                        },
                    ]
                },
                "WeekOne": False,
            },
        ],
        "DatesOfFirstCollectionDays": {"Tuesday": "2026-05-26T00:00:00"},
        "Today": "2026-05-25T12:00:00",
        "AddressName": "Test",
        "PostCode": "CO1 1AA",
    }
    mock_requests.get.return_value = MockResponse(payload)

    entries = colchester_gov_uk.Source(llpgid="test").fetch()

    # Each waste-type entry produces (initial-if-future, +14 days) = 2 dates.
    # Five waste-type slots total -> 10 Collections.
    assert len(entries) == 10

    actual = sorted({(e.date, e.type) for e in entries})
    expected = sorted(
        [
            # Week 1 (WeekOne=True) on 2026-05-26
            (real_date(2026, 5, 26), "Non-recyclable rubbish"),
            (real_date(2026, 5, 26), "Food Waste"),
            (real_date(2026, 6, 9), "Non-recyclable rubbish"),  # +14 days
            (real_date(2026, 6, 9), "Food Waste"),
            # Week 2 (WeekOne=False) on 2026-06-02
            (real_date(2026, 6, 2), "Glass"),
            (real_date(2026, 6, 2), "Mixed recycling"),
            (real_date(2026, 6, 2), "Food Waste"),
            (real_date(2026, 6, 16), "Glass"),  # +14 days
            (real_date(2026, 6, 16), "Mixed recycling"),
            (real_date(2026, 6, 16), "Food Waste"),
        ]
    )
    assert actual == expected


# ---------------------------------------------------------------------------
# Date filtering: past collections in the current cycle drop the initial entry
# but keep the +14 day extrapolation.
# ---------------------------------------------------------------------------


@patch("waste_collection_schedule.source.colchester_gov_uk.datetime", FrozenDatetime)
@patch("waste_collection_schedule.source.colchester_gov_uk.requests")
def test_past_initial_collection_is_dropped_but_extrapolation_kept(mock_requests):
    # Frozen "now" is 2026-05-25. First collection is 2026-05-19 (in the past).
    payload = _payload(["Glass"], [], first_date="2026-05-19T00:00:00")
    mock_requests.get.return_value = MockResponse(payload)

    entries = colchester_gov_uk.Source(llpgid="test").fetch()

    dates = sorted(e.date for e in entries)
    assert real_date(2026, 5, 19) not in dates
    assert real_date(2026, 6, 2) in dates  # +14 days, kept unconditionally
