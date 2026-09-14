"""
Unit tests for London Borough of Redbridge waste collection source.

Redbridge added a separate food waste collection to its household rounds, so the
PDF calendar now contains "Food" rows. These tests lock that behaviour in.

Note: This test file is not auto-discovered by pytest due to pytest.ini configuration
(python_files = test_source_components.py). Run it explicitly:

    pytest tests/test_redbridge_gov_uk.py
    pytest tests/test_redbridge_gov_uk.py -v
"""

import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch

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

from waste_collection_schedule import Icons
from waste_collection_schedule.source import redbridge_gov_uk

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Text extracted from a real Redbridge household calendar PDF (uprn redacted).
# The property has refuse, food, garden and recycling collections on a Monday.
# 31 August 2026 is a bank holiday, so the first collection moves to Tuesday
# 1 September 2026.
CALENDAR_TEXT = """September 2026
Sun Mon Tue Wed Thu Fri Sat
1
 Refuse
 Garden
 Recycling
2 3 4 5
6 7
 Refuse
 Recycling
8 9 10 11 12
13 14
 Refuse
 Food
 Garden
 Recycling
15 16 17 18 19
20 21
 Refuse
 Food
 Recycling
22 23 24 25 26
27 28
 Refuse
 Food
 Garden
 Recycling
29 30
Your collection schedule
 October 2026
Sun Mon Tue Wed Thu Fri Sat
1 2 3
4 5
 Refuse
 Food
 Recycling
6 7 8 9 10
11 12
 Refuse
 Food
 Garden
 Recycling
13 14 15 16 17
18 19
 Refuse
 Food
 Recycling
20 21 22 23 24
25 26
 Refuse
 Food
 Recycling
27 28 29 30 31
Your collection schedule
"""


@pytest.fixture
def collections():
    return redbridge_gov_uk._extract_collections_from_text(CALENDAR_TEXT)


def _dates_of(collections, collection_type):
    return [c.date for c in collections if c.type == collection_type]


# ---------------------------------------------------------------------------
# Food waste
# ---------------------------------------------------------------------------


def test_food_waste_collections_are_parsed(collections):
    assert _dates_of(collections, "Food") == [
        date(2026, 9, 14),
        date(2026, 9, 21),
        date(2026, 9, 28),
        date(2026, 10, 5),
        date(2026, 10, 12),
        date(2026, 10, 19),
        date(2026, 10, 26),
    ]


def test_food_waste_uses_the_kitchen_bio_icon(collections):
    food = [c for c in collections if c.type == "Food"]
    assert food
    for collection in food:
        assert collection.icon == Icons.BIO_KITCHEN


def test_food_waste_label_variant_is_recognised():
    text = """September 2026
Sun Mon Tue Wed Thu Fri Sat
6 7
 Food Waste
"""
    collections = redbridge_gov_uk._extract_collections_from_text(text)
    assert len(collections) == 1
    assert collections[0].type == "Food Waste"
    assert collections[0].icon == Icons.BIO_KITCHEN


def test_food_waste_does_not_displace_the_other_services(collections):
    on_14_september = sorted(c.type for c in collections if c.date == date(2026, 9, 14))
    assert on_14_september == ["Food", "Garden", "Recycling", "Refuse"]


# ---------------------------------------------------------------------------
# The other services
# ---------------------------------------------------------------------------


def test_every_service_type_is_parsed(collections):
    counts = {}
    for collection in collections:
        counts[collection.type] = counts.get(collection.type, 0) + 1
    assert counts == {"Refuse": 9, "Recycling": 9, "Food": 7, "Garden": 4}


def test_icons_match_the_service(collections):
    expected = {
        "Refuse": Icons.GENERAL_WASTE,
        "Recycling": Icons.RECYCLING,
        "Garden": Icons.GARDEN,
        "Food": Icons.BIO_KITCHEN,
    }
    for collection in collections:
        assert collection.icon == expected[collection.type]


def test_bank_holiday_week_keeps_the_shifted_day(collections):
    on_1_september = sorted(c.type for c in collections if c.date == date(2026, 9, 1))
    assert on_1_september == ["Garden", "Recycling", "Refuse"]


def test_unknown_service_lines_are_ignored():
    text = """September 2026
Sun Mon Tue Wed Thu Fri Sat
6 7
 Food
 Textiles
"""
    collections = redbridge_gov_uk._extract_collections_from_text(text)
    assert [c.type for c in collections] == ["Food"]


def test_text_without_a_month_header_yields_nothing():
    assert redbridge_gov_uk._extract_collections_from_text(" Food\n Refuse\n") == []


# ---------------------------------------------------------------------------
# fetch()
# ---------------------------------------------------------------------------


def test_fetch_requests_the_calendar_for_the_uprn_and_returns_food():
    response = MagicMock()
    response.content = b"%PDF-1.4 fake"
    response.raise_for_status = MagicMock()

    with (
        patch.object(
            redbridge_gov_uk.requests, "get", return_value=response
        ) as mock_get,
        patch.object(
            redbridge_gov_uk, "_extract_text_from_pdf", return_value=CALENDAR_TEXT
        ),
    ):
        collections = redbridge_gov_uk.Source(100000000000).fetch()

    mock_get.assert_called_once_with(
        "https://my.redbridge.gov.uk/RecycleRefuse/GetFile",
        params={"uprn": "100000000000"},
    )
    response.raise_for_status.assert_called_once()
    assert any(c.type == "Food" for c in collections)
