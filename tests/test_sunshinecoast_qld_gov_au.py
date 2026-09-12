import os
import sys
from datetime import datetime

import pytest

# Insert repo root to sys.path for absolute imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.waste_collection_schedule.waste_collection_schedule.source import (
    sunshinecoast_qld_gov_au as source,
)


@pytest.mark.parametrize(
    "street_name,expected",
    [
        # already in the API's own form: used as given
        ("hospital rd", ["hospital rd", "hospital"]),
        # a house number and suburb are dropped
        ("12 Hospital Rd, Nambour", ["Hospital Rd", "Hospital"]),
        ("1/20 Main St", ["Main St", "Main"]),
        ("184-202 Main St", ["Main St", "Main"]),
        # a spelled-out street type is abbreviated, then dropped
        ("hospital road", ["hospital road", "hospital rd", "hospital"]),
        # the API is case-insensitive, so the abbreviation's case does not matter
        ("Main Street, Eumundi", ["Main Street", "Main st", "Main"]),
        # nothing to strip
        ("Woombye", ["Woombye"]),
    ],
)
def test_query_candidates(street_name, expected):
    assert source.query_candidates(street_name) == expected


@pytest.mark.parametrize(
    "street_name,expected",
    [
        ("Hospital Rd, Nambour", ("Hospital Rd", "Nambour")),
        ("  Main St ,  Eumundi  ", ("Main St", "Eumundi")),
        ("Hospital Rd", ("Hospital Rd", None)),
    ],
)
def test_split_locality(street_name, expected):
    assert source.split_locality(street_name) == expected


def _locality_for(street_name, locality=None):
    return source.Source(street_name, locality)._locality


def test_locality_comes_from_the_street_name_when_not_given():
    assert _locality_for("12 Hospital Rd, Nambour") == "Nambour"
    # an explicit argument wins
    assert _locality_for("12 Hospital Rd, Nambour", "Woombye") == "Woombye"
    assert _locality_for("Hospital Rd") is None


@pytest.mark.parametrize(
    "day_name,week,expected",
    [
        # 11 Dec 2021 is a Saturday; week 1 is the first such weekday after it
        ("Saturday", "1", datetime(2021, 12, 11)),
        ("Monday", "1", datetime(2021, 12, 13)),
        ("Wednesday", "1", datetime(2021, 12, 15)),
        # week 2 is the following week
        ("Wednesday", "2", datetime(2021, 12, 22)),
        ("Monday", "2", datetime(2021, 12, 20)),
    ],
)
def test_start_date(day_name, week, expected):
    assert source.start_date(day_name, week) == expected


def test_start_date_keeps_the_weekday():
    for week in ("1", "2"):
        assert source.start_date("Thursday", week).strftime("%A") == "Thursday"
