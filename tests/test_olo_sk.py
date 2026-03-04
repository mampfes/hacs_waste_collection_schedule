import sys
import os
from datetime import date, timedelta
from unittest.mock import MagicMock
import types
import pytest

# Mock the waste_collection_schedule module before importing olo_sk
wcs = types.ModuleType('waste_collection_schedule')
wcs.Collection = MagicMock
sys.modules['waste_collection_schedule'] = wcs

exceptions = types.ModuleType('waste_collection_schedule.exceptions')
class SourceArgumentExceptionMultiple(Exception):
    def __init__(self, args, reason):
        super().__init__(f"Arguments required: {args} - {reason}")
exceptions.SourceArgumentExceptionMultiple = SourceArgumentExceptionMultiple
sys.modules['waste_collection_schedule.exceptions'] = exceptions

# Insert source path to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "custom_components", "waste_collection_schedule", "waste_collection_schedule")))

# Now we can import the source module directly
from source import olo_sk


class FixedDate(date):
    _fixed_date = date(2025, 12, 2)  # A Tuesday in week 49 (odd week)

    @classmethod
    def today(cls):
        return cls._fixed_date


@pytest.fixture
def source():
    """Create a Source instance for testing."""
    return olo_sk.Source(street="Test Street", registrationNumber="123456")


# =============================================================================
# Tests for _is_date_in_season
# =============================================================================


def test_is_date_in_season_within(source):
    """Test date within a normal season range."""
    season = ((1, 4), (31, 10))  # April 1 to October 31
    assert source._is_date_in_season(date(2025, 6, 15), season) is True


def test_is_date_in_season_start_boundary(source):
    """Test date on season start boundary."""
    season = ((1, 4), (31, 10))
    assert source._is_date_in_season(date(2025, 4, 1), season) is True


def test_is_date_in_season_end_boundary(source):
    """Test date on season end boundary."""
    season = ((1, 4), (31, 10))
    assert source._is_date_in_season(date(2025, 10, 31), season) is True


def test_is_date_in_season_outside(source):
    """Test date outside a normal season range."""
    season = ((1, 4), (31, 10))  # April 1 to October 31
    assert source._is_date_in_season(date(2025, 12, 15), season) is False


def test_is_date_in_season_year_spanning_winter(source):
    """Test date in winter season that spans year boundary."""
    season = ((1, 11), (28, 2))  # November 1 to February 28
    # December should be in winter season
    assert source._is_date_in_season(date(2025, 12, 15), season) is True
    # January should be in winter season
    assert source._is_date_in_season(date(2025, 1, 15), season) is True


def test_is_date_in_season_year_spanning_outside(source):
    """Test date outside a year-spanning season."""
    season = ((1, 11), (28, 2))  # November 1 to February 28
    # June should not be in winter season
    assert source._is_date_in_season(date(2025, 6, 15), season) is False


# =============================================================================
# Tests for _generate_collection_dates - biweekly patterns
# =============================================================================


def test_generate_dates_every_week(source, monkeypatch):
    """Test generating dates for every week pickup [4,4] (Thursday every week)."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[4,4]", None)

    # Should have Thursdays for 90 days
    assert len(dates) > 0
    # All dates should be Thursdays (isoweekday 4)
    for d in dates:
        assert d.isoweekday() == 4


def test_generate_dates_odd_week_only(source, monkeypatch):
    """Test generating dates for odd week only pickup [5,-]."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[5,-]", None)

    # All dates should be Fridays in odd weeks
    for d in dates:
        assert d.isoweekday() == 5
        assert d.isocalendar()[1] % 2 == 1  # Odd week


def test_generate_dates_even_week_only(source, monkeypatch):
    """Test generating dates for even week only pickup [-,1]."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[-,1]", None)

    # All dates should be Mondays in even weeks
    for d in dates:
        assert d.isoweekday() == 1
        assert d.isocalendar()[1] % 2 == 0  # Even week


def test_generate_dates_different_days(source, monkeypatch):
    """Test generating dates with different days for odd/even weeks [1,5]."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[1,5]", None)

    for d in dates:
        week_num = d.isocalendar()[1]
        if week_num % 2 == 0:
            assert d.isoweekday() == 5  # Friday on even weeks
        else:
            assert d.isoweekday() == 1  # Monday on odd weeks


def test_generate_dates_empty_frequency(source, monkeypatch):
    """Test generating dates with empty frequency string."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("", None)
    assert dates == []


def test_generate_dates_invalid_frequency(source, monkeypatch):
    """Test generating dates with invalid frequency string."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("invalid", None)
    assert dates == []


def test_generate_dates_no_pickup(source, monkeypatch):
    """Test generating dates when no pickup at all [-,-]."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[-,-]", None)
    assert dates == []


# =============================================================================
# Tests for _generate_collection_dates - weekly_multi patterns
# =============================================================================


def test_generate_dates_multi_day(source, monkeypatch):
    """Test generating dates for multi-day pattern [25,25] (Tuesday and Friday)."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[25,25]", None)

    # All dates should be either Tuesday (2) or Friday (5)
    assert len(dates) > 0
    for d in dates:
        assert d.isoweekday() in [2, 5]


def test_generate_dates_multi_day_three_days(source, monkeypatch):
    """Test generating dates for multi-day pattern [135,135] (Mon, Wed, Fri)."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[135,135]", None)

    assert len(dates) > 0
    for d in dates:
        assert d.isoweekday() in [1, 3, 5]


def test_generate_dates_multi_day_odd_only(source, monkeypatch):
    """Test generating dates for multi-day pattern [135,-] (Mon, Wed, Fri on odd weeks only)."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[135,-]", None)

    assert len(dates) > 0
    for d in dates:
        assert d.isoweekday() in [1, 3, 5]
        assert d.isocalendar()[1] % 2 == 1  # All should be odd weeks


def test_generate_dates_multi_day_mixed(source, monkeypatch):
    """Test generating dates for mixed pattern [13,25] (Mon/Wed on odd, Tue/Fri on even)."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[13,25]", None)

    assert len(dates) > 0
    for d in dates:
        week_num = d.isocalendar()[1]
        if week_num % 2 == 1:  # Odd week
            assert d.isoweekday() in [1, 3]  # Monday or Wednesday
        else:  # Even week
            assert d.isoweekday() in [2, 5]  # Tuesday or Friday


# =============================================================================
# Tests for _generate_collection_dates - 4-week cycle patterns
# =============================================================================


def test_generate_dates_4week_known_value_jan13(source, monkeypatch):
    """Regression test: [-,-,2,-] should return Jan 13, 2026.

    Verified against OLO website for registration 2318337.
    Jan 13, 2026 is Tuesday in ISO week 3, (3-1)%4 == 2.
    """

    class Jan1_2026(date):
        @classmethod
        def today(cls):
            return date(2026, 1, 1)

    monkeypatch.setattr(olo_sk.datetime, "date", Jan1_2026)

    dates = source._generate_collection_dates("[-,-,2,-]", None)

    assert date(2026, 1, 13) in dates
    # Should NOT include Jan 20 (which would be 3rd Tuesday / bysetpos=3)
    assert date(2026, 1, 20) not in dates


def test_generate_dates_4week_known_value_dec24(source, monkeypatch):
    """Regression test: [-,-,-,3] should return Dec 24, 2025.

    Dec 24, 2025 is Wednesday in ISO week 52, (52-1)%4 == 3.
    """
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)  # Dec 2, 2025

    dates = source._generate_collection_dates("[-,-,-,3]", None)

    assert date(2025, 12, 24) in dates


def test_generate_dates_4week_position2(source, monkeypatch):
    """Test 4-week cycle pattern [-,-,2,-] (Tuesday in weeks where (week-1)%4 == 2)."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[-,-,2,-]", None)

    assert len(dates) > 0
    for d in dates:
        assert d.isoweekday() == 2  # Tuesday
        assert (d.isocalendar()[1] - 1) % 4 == 2  # Position 2 in 4-week cycle


def test_generate_dates_4week_position0(source, monkeypatch):
    """Test 4-week cycle pattern [4,-,-,-] (Thursday in weeks where (week-1)%4 == 0)."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[4,-,-,-]", None)

    assert len(dates) > 0
    for d in dates:
        assert d.isoweekday() == 4  # Thursday
        assert (d.isocalendar()[1] - 1) % 4 == 0  # Position 0 in 4-week cycle


def test_generate_dates_4week_position3(source, monkeypatch):
    """Test 4-week cycle pattern [-,-,-,5] (Friday in weeks where (week-1)%4 == 3)."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[-,-,-,5]", None)

    assert len(dates) > 0
    for d in dates:
        assert d.isoweekday() == 5  # Friday
        assert (d.isocalendar()[1] - 1) % 4 == 3  # Position 3 in 4-week cycle


def test_generate_dates_4week_positions_0_and_2(source, monkeypatch):
    """Test 4-week cycle pattern [2,-,2,-] (Tuesday in positions 0 and 2)."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    dates = source._generate_collection_dates("[2,-,2,-]", None)

    assert len(dates) > 0
    for d in dates:
        assert d.isoweekday() == 2  # Tuesday
        pos = (d.isocalendar()[1] - 1) % 4
        assert pos in [0, 2]  # Position 0 or 2 in 4-week cycle


# =============================================================================
# Tests for _generate_collection_dates - seasonal patterns
# =============================================================================


def test_generate_dates_seasonal(source, monkeypatch):
    """Test generating dates with seasonal frequency."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    # Thursday in summer, Friday in winter
    dates = source._generate_collection_dates("[4,4];[5,5]", "01/04-31/10, 01/11-31/03")

    # December 2 is in winter, so we should get Fridays
    # Filter to just December dates for testing
    dec_dates = [d for d in dates if d.month == 12]
    for d in dec_dates:
        assert d.isoweekday() == 5  # Friday in winter


# =============================================================================
# Tests for WASTE_TYPES mapping
# =============================================================================


def test_waste_types_all_have_display_name_and_icon():
    """Test that all waste types have display name and icon."""
    for waste_type, (display_name, icon) in olo_sk.WASTE_TYPES.items():
        assert display_name, f"Missing display name for {waste_type}"
        assert icon, f"Missing icon for {waste_type}"
        assert icon.startswith(
            "mdi:"
        ), f"Icon should start with 'mdi:' for {waste_type}"


def test_waste_types_expected_count():
    """Test that we have the expected number of waste types."""
    assert len(olo_sk.WASTE_TYPES) == 6


def test_waste_types_known_types():
    """Test that all expected waste types are defined."""
    expected_types = ["Zmiešaný odpad", "KBRO", "BRO", "Plast", "Papier", "Sklo"]
    for waste_type in expected_types:
        assert waste_type in olo_sk.WASTE_TYPES, f"Missing waste type: {waste_type}"
