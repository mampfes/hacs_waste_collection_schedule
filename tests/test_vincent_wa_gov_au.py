import os
import sys
from datetime import date, datetime, timedelta

import pytest

# Insert repo root to sys.path for absolute imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.waste_collection_schedule.waste_collection_schedule.preprocessors import (
    RecurrenceExpander,
)
from custom_components.waste_collection_schedule.waste_collection_schedule.source import (
    vincent_wa_gov_au,
)

_expand = RecurrenceExpander(vincent_wa_gov_au._describe)


def _dates(zone: dict, label: str) -> list[date]:
    return sorted(d for d, key in _expand([zone], None) if key == label)


def test_weekly_starts_on_the_given_date():
    zone = {
        "FOGO Collection Day": "FOGO Collection Day:16 Sep 2026 - Weekly (Wednesday)"
    }
    entries = _dates(zone, "FOGO")

    assert len(entries) == 26
    assert entries[0] == date(2026, 9, 16)
    assert entries[1] == date(2026, 9, 23)


def test_extra_space_before_the_day_still_parses():
    # the council's Recycling value has two spaces before "(Wednesday)"
    zone = {
        "Recycling Collection Day": (
            "Recycling Collection Day:16 Sep 2026 - Weekly  (Wednesday)"
        )
    }
    entries = _dates(zone, "Recycling")

    assert len(entries) == 26
    assert entries[0] == date(2026, 9, 16)


def test_fortnightly_steps_by_two_weeks():
    zone = {
        "General Waste Collection Day": (
            "General Waste Collection Day:21 Sep 2026 - Fortnightly (Monday Week 1)"
        )
    }
    entries = _dates(zone, "General Waste")

    assert len(entries) == 13
    assert entries[0] == date(2026, 9, 21)
    assert entries[1] == date(2026, 10, 5)


def test_twice_weekly_covers_both_days():
    zone = {
        "General Waste Collection Day": (
            "General Waste Collection Day:11 Sep 2026 - 2 x weekly (Wednesday/friday)"
        )
    }
    entries = _dates(zone, "General Waste")

    # 26 of each day; the second day is lower-cased in the council's data
    assert len(entries) == 52
    assert {d.weekday() for d in entries} == {2, 4}
    # dates are generated from today onwards, never in the past
    assert min(entries) >= datetime.now().date()
    assert max(entries) <= datetime.now().date() + timedelta(weeks=26)


def test_label_prefix_is_optional():
    zone = {"FOGO Collection Day": "16 Sep 2026 - Weekly (Wednesday)"}
    assert len(_dates(zone, "FOGO")) == 26


@pytest.mark.parametrize(
    "text",
    [
        "General Waste Collection Day:None",
        "General Waste Collection Day:",
        # a frequency the source does not generate dates for
        "General Waste Collection Day:16 Sep 2026 - On request (Wednesday)",
        # an unparsable date
        "General Waste Collection Day:31 Feb 2026 - Weekly (Wednesday)",
    ],
)
def test_unparseable_values_yield_no_entries(text):
    zone = {"General Waste Collection Day": text}
    assert _dates(zone, "General Waste") == []
