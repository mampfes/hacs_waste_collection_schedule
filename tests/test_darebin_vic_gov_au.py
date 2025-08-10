import sys
import os
from datetime import date, timedelta
import pytest

# Insert repo root to sys.path for absolute imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.waste_collection_schedule.waste_collection_schedule.source import darebin_vic_gov_au


class FixedDate(date):
    @classmethod
    def today(cls):
        # Fix today's date for test consistency
        return date(2025, 8, 9)


def test_past_date_moves_forward(monkeypatch):
    monkeypatch.setattr(darebin_vic_gov_au, "date", FixedDate)
    start_date = date(2025, 8, 1)
    n = 2
    delta = timedelta(days=7)
    expected = [date(2025, 8, 15), date(2025, 8, 22)]

    results = darebin_vic_gov_au._get_next_n_dates(start_date, n, delta)
    assert results == expected, (
        f"Expected dates {expected} for start_date={start_date}, "
        f"n={n}, delta={delta}, but got {results}"
    )


def test_start_date_is_today(monkeypatch):
    monkeypatch.setattr(darebin_vic_gov_au, "date", FixedDate)
    start_date = date(2025, 8, 9)
    n = 2
    delta = timedelta(days=7)
    expected = [date(2025, 8, 9), date(2025, 8, 16)]

    results = darebin_vic_gov_au._get_next_n_dates(start_date, n, delta)
    assert results == expected, (
        f"Expected {expected} for start_date={start_date}, "
        f"n={n}, delta={delta}, but got {results}"
    )


def test_start_date_after_today_no_skip(monkeypatch):
    monkeypatch.setattr(darebin_vic_gov_au, "date", FixedDate)
    start_date = date(2025, 8, 15)
    n = 2
    delta = timedelta(days=14)
    expected = [date(2025, 8, 15), date(2025, 8, 29)]

    results = darebin_vic_gov_au._get_next_n_dates(start_date, n, delta)
    assert results == expected, (
        f"Expected {expected} for start_date={start_date}, "
        f"n={n}, delta={delta}, but got {results}"
    )


def test_multiple_weeks_ahead(monkeypatch):
    monkeypatch.setattr(darebin_vic_gov_au, "date", FixedDate)
    start_date = date(2025, 9, 1)
    n = 3
    delta = timedelta(weeks=6)
    expected = [date(2025, 9, 1), date(2025, 10, 13), date(2025, 11, 24)]

    results = darebin_vic_gov_au._get_next_n_dates(start_date, n, delta)
    assert results == expected, (
        f"Expected {expected} for start_date={start_date}, "
        f"n={n}, delta={delta}, but got {results}"
    )


def test_future_date_less_than_delta(monkeypatch):
    monkeypatch.setattr(darebin_vic_gov_au, "date", FixedDate)
    start_date = date(2025, 8, 15)
    n = 2
    delta = timedelta(days=14)
    expected = [date(2025, 8, 15), date(2025, 8, 29)]

    results = darebin_vic_gov_au._get_next_n_dates(start_date, n, delta)
    assert results == expected, (
        f"Expected {expected} for start_date={start_date}, "
        f"n={n}, delta={delta}, but got {results}"
    )


def test_get_previous_date_for_day_of_week_monday(monkeypatch):
    monkeypatch.setattr(darebin_vic_gov_au, "date", FixedDate)
    collection_day = "Monday"
    expected = date(2025,8,4)

    results = darebin_vic_gov_au._get_previous_date_for_day_of_week(darebin_vic_gov_au.WEEKDAY_MAP[collection_day])
    assert results == expected, (
        f"Expected {expected} for day_of_week={collection_day}, "
        f"but got {results}"
    )


def test_get_previous_date_for_day_of_week_tuesday(monkeypatch):
    monkeypatch.setattr(darebin_vic_gov_au, "date", FixedDate)
    collection_day = "Tuesday"
    expected = date(2025,8,5)

    results = darebin_vic_gov_au._get_previous_date_for_day_of_week(darebin_vic_gov_au.WEEKDAY_MAP[collection_day])
    assert results == expected, (
        f"Expected {expected} for day_of_week={collection_day}, "
        f"but got {results}"
    )


def test_get_previous_date_for_day_of_week_wednesday(monkeypatch):
    monkeypatch.setattr(darebin_vic_gov_au, "date", FixedDate)
    collection_day = "Wednesday"
    expected = date(2025,8,6)

    results = darebin_vic_gov_au._get_previous_date_for_day_of_week(darebin_vic_gov_au.WEEKDAY_MAP[collection_day])
    assert results == expected, (
        f"Expected {expected} for day_of_week={collection_day}, "
        f"but got {results}"
    )


def test_get_previous_date_for_day_of_week_thursday(monkeypatch):
    monkeypatch.setattr(darebin_vic_gov_au, "date", FixedDate)
    collection_day = "Thursday"
    expected = date(2025,8,7)

    results = darebin_vic_gov_au._get_previous_date_for_day_of_week(darebin_vic_gov_au.WEEKDAY_MAP[collection_day])
    assert results == expected, (
        f"Expected {expected} for day_of_week={collection_day}, "
        f"but got {results}"
    )


def test_get_previous_date_for_day_of_week_friday(monkeypatch):
    monkeypatch.setattr(darebin_vic_gov_au, "date", FixedDate)
    collection_day = "Friday"
    expected = date(2025,8,8)

    results = darebin_vic_gov_au._get_previous_date_for_day_of_week(darebin_vic_gov_au.WEEKDAY_MAP[collection_day])
    assert results == expected, (
        f"Expected {expected} for day_of_week={collection_day}, "
        f"but got {results}"
    )


def test_get_previous_date_for_day_of_week_saturday(monkeypatch):
    monkeypatch.setattr(darebin_vic_gov_au, "date", FixedDate)
    collection_day = "Saturday"
    expected = date(2025,8,9)

    results = darebin_vic_gov_au._get_previous_date_for_day_of_week(darebin_vic_gov_au.WEEKDAY_MAP[collection_day])
    assert results == expected, (
        f"Expected {expected} for day_of_week={collection_day}, "
        f"but got {results}"
    )


def test_get_previous_date_for_day_of_week_sunday(monkeypatch):
    monkeypatch.setattr(darebin_vic_gov_au, "date", FixedDate)
    collection_day = "Sunday"
    expected = date(2025,8,3)

    results = darebin_vic_gov_au._get_previous_date_for_day_of_week(darebin_vic_gov_au.WEEKDAY_MAP[collection_day])
    assert results == expected, (
        f"Expected {expected} for day_of_week={collection_day},  "
        f"but got {results}"
    )