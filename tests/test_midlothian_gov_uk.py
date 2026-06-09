"""
Test for Midlothian Council waste collection source.

Note: This test file is not auto-discovered by pytest due to pytest.ini configuration.
To run this test specifically:
    pytest tests/test_midlothian_gov_uk.py

Or run it with the test function name:
    pytest tests/test_midlothian_gov_uk.py::test_fetch_returns_collections
"""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.waste_collection_schedule.waste_collection_schedule.source import (  # noqa: E402
    midlothian_gov_uk,
)

# Test data
TEST_UPRN = "120001401"
TEST_POSTCODE = "EH26 8AG"


@pytest.fixture(scope="module")
def collections():
    """Fixture that fetches collections once and shares across all tests."""
    source = midlothian_gov_uk.Source(uprn=TEST_UPRN, postcode=TEST_POSTCODE)
    return source.fetch()


def test_fetch_returns_collections(collections):
    """Test that fetch returns a non-empty list of collections."""
    assert collections is not None
    assert isinstance(collections, list)
    assert len(collections) > 0


def test_collections_have_required_fields(collections):
    """Test that each collection has date, type, and icon fields."""
    for collection in collections:
        assert collection.date is not None, "Collection date should not be None"
        assert collection.type is not None, "Collection type should not be None"
        assert collection.icon is not None, "Collection icon should not be None"


def test_collection_dates_are_valid(collections):
    """Test that collection dates are valid date objects and within a reasonable range."""
    # Given
    today = date.today()
    from datetime import timedelta

    # Allow a 1-day grace period to handle timezone edge cases and collections
    # that occur "today" but may have already passed when the test runs
    earliest_allowed = today - timedelta(days=1)
    # Verify we're not getting data too far in the future (sanity check)
    latest_allowed = today + timedelta(days=400)  # ~13 months

    # Assert all collection dates are valid date objects
    for collection in collections:
        assert isinstance(
            collection.date, date
        ), "Collection date should be a date object"
        assert earliest_allowed <= collection.date <= latest_allowed, (
            f"Collection date {collection.date} is outside reasonable range "
            f"({earliest_allowed} to {latest_allowed})"
        )

    # Group collections by type
    from collections import defaultdict

    type_to_dates = defaultdict(list)
    for collection in collections:
        type_to_dates[collection.type].append(collection.date)

    # For each type, verify we have at least one upcoming collection
    # Note: Midlothian API returns collections from today onwards (we pass fromDate=today),
    # so we expect dates >= today, but allow a 1-day grace period for edge cases
    for ctype, dates in type_to_dates.items():
        soonest = min(dates)
        assert (
            soonest >= earliest_allowed
        ), f"Soonest collection date for {ctype} is unexpectedly old: {soonest}"


def test_collection_types_are_recognized(collections):
    """Test that collection types match expected waste types."""
    # Given
    expected_types = {
        "Food Collection Service",
        "Glass Collection Service",
        "Residual Collection Service",
        "Garden Collection Service",
        "Recycling Collection Service",
        "Card Collection Service",
    }

    # When
    collection_types = {c.type for c in collections}

    # Then
    assert collection_types.issubset(
        expected_types
    ), f"Unexpected collection types found: {collection_types - expected_types}"


def test_icons_match_collection_types(collections):
    """Test that icons are correctly mapped to their collection types."""
    for collection in collections:
        expected_icon = midlothian_gov_uk.ICON_MAP.get(collection.type)
        assert (
            collection.icon == expected_icon
        ), f"Icon mismatch for {collection.type}: expected {expected_icon}, got {collection.icon}"


def test_source_initialization():
    """Test that Source class initializes correctly with UPRN and postcode."""
    # Given
    uprn = TEST_UPRN
    postcode = TEST_POSTCODE

    # When
    source = midlothian_gov_uk.Source(uprn=uprn, postcode=postcode)

    # Then
    assert isinstance(source, midlothian_gov_uk.Source)


def test_multiple_collections_returned(collections):
    """Test that multiple collections are returned (typically multiple weeks/services)."""
    assert (
        len(collections) >= 2
    ), f"Expected at least 2 collections, but got {len(collections)}"
