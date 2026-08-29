"""Offline tests for the montreal_ca seasonal schedule parser.

Montreal publishes its collection schedule as English prose in the
Info-Collecte GeoJSON feeds, so the whole source hinges on
``Source.parse_collection``. The MESSAGE_EN strings below are verbatim
captures from the live feeds for the 2026 season, which lets these run
without touching the network.
"""

import os
import sys
import types
from datetime import date
from unittest.mock import MagicMock

import pytest

wcs = types.ModuleType("waste_collection_schedule")


class Collection:
    """Minimal stand-in for the real Collection dataclass."""

    def __init__(self, date, t, icon=None, picture=None):
        self.date = date
        self.t = t
        self.icon = icon


wcs.Collection = Collection  # type: ignore[attr-defined]
wcs.Icons = MagicMock()  # type: ignore[attr-defined]
sys.modules["waste_collection_schedule"] = wcs
sys.modules["waste_collection_schedule.exceptions"] = types.ModuleType(
    "waste_collection_schedule.exceptions"
)

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
            "waste_collection_schedule",
            "waste_collection_schedule",
        )
    ),
)

from source import montreal_ca  # noqa: E402

# Anjou sector ANJ-1: seasonal ranges either side of a biweekly summer list.
ANJ1_GREEN = " Collection days in 2026 :   \n  - Spring : from April 1 to May 27, every week on Wednesday  \n  -  Summer : June 10 and 24; July 8 and 22; August 5 and 19; September 2 and 16 (every two weeks on Wednesday)  - Autumn: from September 30 to November 25, every week on Wednesday  \n   \n Hours :  Take out containers between 7 p.m. the evening before and 7 a.m. the day of collection  \nContainers accepted : \n - Reusable rigid containers \n - Paper bags \n - Cardboard boxes\n *The use of plastic bags as containers is prohibited"

# Rosemont sector RPP-RE-22-RV: same shape, but the biweekly season is
# phrased "every second week" and the list ends at a line break.
RPP_GREEN = " Collection days in 2026  : \n - Spring : from April 8 to May 27, every week on Wednesday\n -  Summer, every second week : June 3 and 17; July 1, 15 and 29; August 12 and 26; September 9 and 23\n - Autumn : from September 30 to November 25, every week on Wednesday\n\nDeposit place: See instructions for Waste collection \nHours :  Take out containers between 5 a.m. and 8 a.m. the day of collection \nContainers accepted : \n - Reusable rigid containers \n - Paper bags \n - Cardboard boxes \n - Plastic bags are PROHIBITED"

# Mercier-Hochelaga sector MHM-42-S: plain per-month date lists, no seasons.
MHM_GREEN = "Collection day(s) 2026 :  the following tuesdays :\n - April 21 and 28;\n - May 5, 12, 19 and 26 ; \n - June 2, 9 and 23;\n - July 7 and 21;\n - August 4, 18 and 25;\n - September 1, 8, 15, 22 and 29; \n - October 6, 13, 20 and 27;\n - November 3, 10 and 17. \nHours : Take out containers between 7 p.m. the evening before and 7 a.m. the day of collection. \nContainers accepted : \n - Reusable rigid containers \n - Paper bags \n - Cardboard boxes \nPlastic bags are not accepted."


def parse(message):
    """Return the set of dates the parser produces for a MESSAGE_EN string."""
    source = montreal_ca.Source(sector="TEST")
    return {c.date for c in source.parse_collection("Green", message)}


@pytest.fixture
def anj1():
    return parse(ANJ1_GREEN)


@pytest.fixture
def rpp():
    return parse(RPP_GREEN)


def test_anj1_matches_published_schedule(anj1):
    """ANJ-1 spells out every collection day; parse all of them, and only them."""
    expected = (
        {date(2026, 4, d) for d in (1, 8, 15, 22, 29)}
        | {date(2026, 5, d) for d in (6, 13, 20, 27)}
        | {date(2026, 6, d) for d in (10, 24)}
        | {date(2026, 7, d) for d in (8, 22)}
        | {date(2026, 8, d) for d in (5, 19)}
        | {date(2026, 9, d) for d in (2, 16, 30)}
        | {date(2026, 10, d) for d in (7, 14, 21, 28)}
        | {date(2026, 11, d) for d in (4, 11, 18, 25)}
    )
    assert anj1 == expected


def test_range_starting_on_a_two_digit_day(anj1):
    """A range starting on a two-digit day must arm on that day.

    A greedy ``.*(\\d+).*`` captured only the trailing "0" of "September 30",
    so day_start was 0, never matched a real day, and the whole autumn range
    produced nothing.
    """
    assert date(2026, 9, 30) in anj1
    assert date(2026, 10, 7) in anj1


def test_final_month_of_a_range_is_kept(anj1):
    """The stop month must be collected up to and including the stop day.

    ``day_stop >= day`` was already true on the 1st of the stop month, which
    cleared the range before any date in it could be emitted.
    """
    assert {date(2026, 11, d) for d in (4, 11, 18, 25)} <= anj1
    assert date(2026, 12, 2) not in anj1


def test_biweekly_summer_is_not_expanded_to_weekly(anj1):
    """A biweekly line contains "week" but must not take the weekly branch."""
    june = {d.day for d in anj1 if d.month == 6}
    assert june == {10, 24}


def test_no_dates_bleed_between_months(anj1):
    """A greedy capture ran to the last month name in the line.

    June inherited the day numbers of July, August and September, inventing
    June 19 and June 22.
    """
    assert date(2026, 6, 19) not in anj1
    assert date(2026, 6, 22) not in anj1


def test_every_second_week_phrasing(rpp):
    """Rosemont writes "every second week" rather than "every two weeks"."""
    assert {d.day for d in rpp if d.month == 6} == {3, 17}
    assert {d.day for d in rpp if d.month == 7} == {1, 15, 29}
    assert {d.day for d in rpp if d.month == 8} == {12, 26}


def test_last_month_before_a_line_break(rpp):
    """September ends the biweekly list and is followed by a newline."""
    assert {date(2026, 9, 9), date(2026, 9, 23)} <= rpp


def test_plain_date_lists_are_unaffected():
    """Sectors without seasons must keep parsing exactly as before."""
    parsed = parse(MHM_GREEN)
    assert parsed
    assert all(d.weekday() == 1 for d in parsed)
