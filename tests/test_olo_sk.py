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
class SourceArgumentRequired(Exception):
    def __init__(self, arg):
        super().__init__(f"Argument required: {arg}")
exceptions.SourceArgumentRequired = SourceArgumentRequired
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
# Tests for _parse_frequency
# =============================================================================

def test_parse_frequency_simple(source):
    """Test parsing simple frequency like [4,4] (Thursday every week)."""
    result = source._parse_frequency("[4,4]")
    assert result == [(4, 4)]


def test_parse_frequency_even_only(source):
    """Test parsing frequency with pickup only on even weeks [-,5]."""
    result = source._parse_frequency("[-,5]")
    assert result == [(None, 5)]


def test_parse_frequency_odd_only(source):
    """Test parsing frequency with pickup only on odd weeks [3,-]."""
    result = source._parse_frequency("[3,-]")
    assert result == [(3, None)]


def test_parse_frequency_different_days(source):
    """Test parsing frequency with different days for even/odd weeks [1,5]."""
    result = source._parse_frequency("[1,5]")
    assert result == [(1, 5)]


def test_parse_frequency_seasonal(source):
    """Test parsing seasonal frequency with multiple patterns."""
    result = source._parse_frequency("[14,14];[1,1]")
    # Note: 14 is not a valid weekday, but the parser should still extract it
    assert result == [(14, 14), (1, 1)]


def test_parse_frequency_seasonal_with_spaces(source):
    """Test parsing seasonal frequency with spaces."""
    result = source._parse_frequency("[4,4]; [1,1]")
    assert result == [(4, 4), (1, 1)]


def test_parse_frequency_empty(source):
    """Test parsing empty frequency string."""
    result = source._parse_frequency("")
    assert result == []


def test_parse_frequency_invalid(source):
    """Test parsing invalid frequency string."""
    result = source._parse_frequency("invalid")
    assert result == []


# =============================================================================
# Tests for _parse_season
# =============================================================================

def test_parse_season_single(source):
    """Test parsing single season range."""
    result = source._parse_season("01/04-31/10")
    assert result == [((1, 4), (31, 10))]


def test_parse_season_multiple(source):
    """Test parsing multiple season ranges."""
    result = source._parse_season("01/04-31/10, 01/11-31/03")
    assert result == [((1, 4), (31, 10)), ((1, 11), (31, 3))]


def test_parse_season_with_spaces(source):
    """Test parsing season ranges with various spacing."""
    result = source._parse_season("01/04-31/10,  01/11-31/03")
    assert result == [((1, 4), (31, 10)), ((1, 11), (31, 3))]


def test_parse_season_none(source):
    """Test parsing None season string."""
    result = source._parse_season(None)
    assert result == []


def test_parse_season_empty(source):
    """Test parsing empty season string."""
    result = source._parse_season("")
    assert result == []


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
# Tests for _generate_dates
# =============================================================================

def test_generate_dates_every_week(source, monkeypatch):
    """Test generating dates for every week pickup (same day even/odd)."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    # Thursday every week [4,4]
    patterns = [(4, 4)]
    seasons = []

    dates = source._generate_dates(patterns, seasons)

    # Should have Thursdays for 90 days
    assert len(dates) > 0
    # All dates should be Thursdays (isoweekday 4)
    for d in dates:
        assert d.isoweekday() == 4


def test_generate_dates_odd_week_only(source, monkeypatch):
    """Test generating dates for odd week only pickup."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    # Friday only on odd weeks [-,5] -> (None, 5)
    patterns = [(None, 5)]
    seasons = []

    dates = source._generate_dates(patterns, seasons)

    # All dates should be Fridays in odd weeks
    for d in dates:
        assert d.isoweekday() == 5
        assert d.isocalendar()[1] % 2 == 1  # Odd week


def test_generate_dates_even_week_only(source, monkeypatch):
    """Test generating dates for even week only pickup."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    # Monday only on even weeks [1,-] -> (1, None)
    patterns = [(1, None)]
    seasons = []

    dates = source._generate_dates(patterns, seasons)

    # All dates should be Mondays in even weeks
    for d in dates:
        assert d.isoweekday() == 1
        assert d.isocalendar()[1] % 2 == 0  # Even week


def test_generate_dates_different_days(source, monkeypatch):
    """Test generating dates with different days for even/odd weeks."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    # Monday on even weeks, Friday on odd weeks [1,5]
    patterns = [(1, 5)]
    seasons = []

    dates = source._generate_dates(patterns, seasons)

    for d in dates:
        week_num = d.isocalendar()[1]
        if week_num % 2 == 0:
            assert d.isoweekday() == 1  # Monday on even weeks
        else:
            assert d.isoweekday() == 5  # Friday on odd weeks


def test_generate_dates_empty_patterns(source, monkeypatch):
    """Test generating dates with no patterns."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    patterns = []
    seasons = []

    dates = source._generate_dates(patterns, seasons)
    assert dates == []


def test_generate_dates_no_pickup(source, monkeypatch):
    """Test generating dates when no pickup at all [-,-]."""
    monkeypatch.setattr(olo_sk.datetime, "date", FixedDate)

    patterns = [(None, None)]
    seasons = []

    dates = source._generate_dates(patterns, seasons)
    assert dates == []


# =============================================================================
# Tests for WASTE_TYPES mapping
# =============================================================================

def test_waste_types_all_have_display_name_and_icon():
    """Test that all waste types have display name and icon."""
    for waste_type, (display_name, icon) in olo_sk.WASTE_TYPES.items():
        assert display_name, f"Missing display name for {waste_type}"
        assert icon, f"Missing icon for {waste_type}"
        assert icon.startswith("mdi:"), f"Icon should start with 'mdi:' for {waste_type}"


def test_waste_types_expected_count():
    """Test that we have the expected number of waste types."""
    assert len(olo_sk.WASTE_TYPES) == 6
