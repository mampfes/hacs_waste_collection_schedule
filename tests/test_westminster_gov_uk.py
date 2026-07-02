"""
Unit tests for Westminster City Council waste collection source.

Note: This test file is not auto-discovered by pytest due to pytest.ini configuration
(python_files = test_source_components.py). Run it explicitly:

    pytest tests/test_westminster_gov_uk.py -v
"""

import os
import sys
from datetime import date as real_date
from unittest.mock import patch

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

from waste_collection_schedule import Icons  # noqa: E402
from waste_collection_schedule.exceptions import SourceArgumentNotFound  # noqa: E402
from waste_collection_schedule.source import westminster_gov_uk  # noqa: E402


# ---------------------------------------------------------------------------
# Section 1: _parse_days (pure function)
# ---------------------------------------------------------------------------


def test_parse_days_comma_list():
    assert westminster_gov_uk._parse_days("Tue, Fri") == {1, 4}


def test_parse_days_hyphen_range_no_spaces():
    assert westminster_gov_uk._parse_days("Mon-Fri") == {0, 1, 2, 3, 4}


def test_parse_days_hyphen_range_with_spaces():
    assert westminster_gov_uk._parse_days("Mon - Fri") == {0, 1, 2, 3, 4}


def test_parse_days_weekend():
    assert westminster_gov_uk._parse_days("Sat, Sun") == {5, 6}


def test_parse_days_full_comma_list():
    assert westminster_gov_uk._parse_days("Mon, Tue, Wed, Thu, Fri") == {0, 1, 2, 3, 4}


def test_parse_days_single_day():
    assert westminster_gov_uk._parse_days("Tue") == {1}


def test_parse_days_empty_and_nbsp():
    assert westminster_gov_uk._parse_days("") == set()
    assert westminster_gov_uk._parse_days("\xa0") == set()


def test_parse_days_ignores_unknown_tokens():
    assert westminster_gov_uk._parse_days("Someday, Tue") == {1}
