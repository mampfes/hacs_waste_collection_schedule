import sys
import os
from datetime import date, timedelta
import pytest

# Insert repo root to sys.path for absolute imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.waste_collection_schedule.waste_collection_schedule.source import moonee_valley_vic_gov_au


class FixedDate(date):
    @classmethod
    def today(cls):
        # Fix today's date for test consistency
        return date(2025, 1, 5)


def test_past_date_moves_forward(monkeypatch):
    monkeypatch.setattr(moonee_valley_vic_gov_au, "date", FixedDate)
    start_date = date(2024, 12, 1)
    n = 2
    delta = timedelta(days=7)
    expected = [date(2025, 1, 5), date(2025, 1, 12)]

    results = moonee_valley_vic_gov_au._get_next_n_dates(start_date, n, delta)
    assert results == expected, (
        f"Expected dates {expected} for start_date={start_date}, "
        f"n={n}, delta={delta}, but got {results}"
    )


def test_start_date_is_today(monkeypatch):
    monkeypatch.setattr(moonee_valley_vic_gov_au, "date", FixedDate)
    start_date = date(2025, 1, 5)
    n = 2
    delta = timedelta(days=7)
    expected = [date(2025, 1, 5), date(2025, 1, 12)]

    results = moonee_valley_vic_gov_au._get_next_n_dates(start_date, n, delta)
    assert results == expected, (
        f"Expected {expected} for start_date={start_date}, "
        f"n={n}, delta={delta}, but got {results}"
    )


def test_start_date_after_today_no_skip(monkeypatch):
    monkeypatch.setattr(moonee_valley_vic_gov_au, "date", FixedDate)
    start_date = date(2025, 1, 10)
    n = 2
    delta = timedelta(days=14)
    expected = [date(2025, 1, 10), date(2025, 1, 24)]

    results = moonee_valley_vic_gov_au._get_next_n_dates(start_date, n, delta)
    assert results == expected, (
        f"Expected {expected} for start_date={start_date}, "
        f"n={n}, delta={delta}, but got {results}"
    )


def test_multiple_weeks_ahead(monkeypatch):
    monkeypatch.setattr(moonee_valley_vic_gov_au, "date", FixedDate)
    start_date = date(2025, 2, 1)
    n = 3
    delta = timedelta(weeks=6)
    expected = [date(2025, 2, 1), date(2025, 3, 15), date(2025, 4, 26)]

    results = moonee_valley_vic_gov_au._get_next_n_dates(start_date, n, delta)
    assert results == expected, (
        f"Expected {expected} for start_date={start_date}, "
        f"n={n}, delta={delta}, but got {results}"
    )


def test_future_date_less_than_delta(monkeypatch):
    monkeypatch.setattr(moonee_valley_vic_gov_au, "date", FixedDate)
    start_date = date(2025, 1, 15)
    n = 2
    delta = timedelta(days=14)
    expected = [date(2025, 1, 15), date(2025, 1, 29)]

    results = moonee_valley_vic_gov_au._get_next_n_dates(start_date, n, delta)
    assert results == expected, (
        f"Expected {expected} for start_date={start_date}, "
        f"n={n}, delta={delta}, but got {results}"
    )


def test_get_previous_date_for_day_of_week_tuesday(monkeypatch):
    monkeypatch.setattr(moonee_valley_vic_gov_au, "date", FixedDate)
    collection_day = "Tuesday"
    expected = date(2024, 12, 31)  # Last Tuesday before 2025-01-05

    results = moonee_valley_vic_gov_au._get_previous_date_for_day_of_week(
        moonee_valley_vic_gov_au.WEEKDAY_MAP[collection_day]
    )
    assert results == expected, (
        f"Expected {expected} for day_of_week={collection_day}, "
        f"but got {results}"
    )
