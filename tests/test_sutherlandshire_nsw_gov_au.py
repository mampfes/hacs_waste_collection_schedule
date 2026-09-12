"""Tests for the Sutherland Shire recycling/garden fortnight.

The council's GIS layer gives a property's collection day and zone but says
nothing about which fortnight is which, so the source anchors the alternation
to a date. Getting that anchor wrong swaps recycling and garden waste for
every property in the shire, and no live TEST_CASE notices: the fetch still
returns a full year of collections, just with the two bins the wrong way
round.

The dates below are read off the council's published 2026/27 calendars, where
a yellow-highlighted week is the yellow-lid recycling week and a green one the
green-lid garden week:

Zone 1: .../pdf_file/0020/121934/SSC-Waste-Calendar-2026-27-Zone1-Print.pdf
Zone 2: .../pdf_file/0021/121935/SSC-Waste-Calendar-2026-27-Zone2-Print.pdf
"""

import os
import sys
from datetime import date, timedelta
from itertools import pairwise

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

from waste_collection_schedule.source.sutherlandshire_nsw_gov_au import (
    _generate_collections,
)

MONDAY = 0
FRIDAY = 4


def _type_on(collection_date, zone, weekday=MONDAY, weekly_recycling=False):
    """The fortnightly bin the source schedules for that date."""
    entries = _generate_collections(
        weekday,
        zone,
        collection_date,
        collection_date,
        weekly_recycling,
    )
    types = [e.type for e in entries if e.type != "Garbage"]
    assert types, f"no fortnightly collection generated for {collection_date}"
    return types


# Mondays taken from the printed calendars, either side of the reported case.
ZONE1_MONDAYS = {
    date(2026, 8, 31): "Recycling",
    date(2026, 9, 7): "Garden Waste",
    date(2026, 9, 14): "Recycling",
    date(2026, 9, 21): "Garden Waste",
    date(2026, 9, 28): "Recycling",
    date(2026, 7, 6): "Recycling",
    date(2027, 6, 28): "Garden Waste",
}


@pytest.mark.parametrize("day,expected", sorted(ZONE1_MONDAYS.items()))
def test_zone1_matches_the_published_calendar(day, expected):
    assert _type_on(day, "1") == [expected]


@pytest.mark.parametrize("day,expected", sorted(ZONE1_MONDAYS.items()))
def test_zone2_is_the_opposite_fortnight(day, expected):
    other = "Garden Waste" if expected == "Recycling" else "Recycling"
    assert _type_on(day, "2") == [other]


def test_reported_case_11_nelson_street_engadine():
    # Zone 1, Monday. The council's calendar has 14 September 2026 as a yellow
    # week; the source used to schedule garden waste.
    assert _type_on(date(2026, 9, 14), "1") == ["Recycling"]


def test_a_non_monday_takes_its_own_weeks_parity():
    # 4-20 Eton Street, Sutherland is Zone 1 and collected on a Friday. The
    # anchor is a Monday, so a Friday must resolve to the week it falls in,
    # not the one before.
    assert _type_on(date(2026, 9, 4), "1", weekday=FRIDAY) == ["Recycling"]
    assert _type_on(date(2026, 9, 11), "1", weekday=FRIDAY) == ["Garden Waste"]


def test_weekly_recycling_properties_get_both_in_a_garden_week():
    assert sorted(_type_on(date(2026, 9, 7), "1", weekly_recycling=True)) == [
        "Garden Waste",
        "Recycling",
    ]


def test_the_two_bins_alternate_every_week_for_a_year():
    start = date(2026, 7, 6)
    seen = [_type_on(start + timedelta(weeks=n), "1")[0] for n in range(52)]
    assert all(a != b for a, b in pairwise(seen))


def test_garbage_is_collected_every_week():
    entries = _generate_collections(
        MONDAY, "1", date(2026, 9, 7), date(2026, 9, 28), False
    )
    garbage = sorted(e.date for e in entries if e.type == "Garbage")
    assert garbage == [
        date(2026, 9, 7),
        date(2026, 9, 14),
        date(2026, 9, 21),
        date(2026, 9, 28),
    ]
