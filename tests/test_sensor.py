"""Tests for sensor logic."""

from custom_components.waste_collection_schedule.sensor import get_days_to_text


def test_get_days_to_text_today():
    """Test that 0 days returns 'Today'."""
    assert get_days_to_text(0) == "Today"


def test_get_days_to_text_tomorrow():
    """Test that 1 day returns 'Tomorrow'."""
    assert get_days_to_text(1) == "Tomorrow"


def test_get_days_to_text_future():
    """Test that >1 days returns formatted string."""
    assert get_days_to_text(2) == "in 2 days"
    assert get_days_to_text(7) == "in 7 days"
    assert get_days_to_text(11) == "in 11 days"
