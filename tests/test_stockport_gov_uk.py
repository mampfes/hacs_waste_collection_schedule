import os
import sys
from datetime import date
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

from waste_collection_schedule import Collection  # noqa: E402
from waste_collection_schedule.source import stockport_gov_uk  # noqa: E402

# Sample HTML that mimics the Stockport council website structure
# This is the key test fixture - it should match the real website structure
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Bin Collections</title></head>
<body>
    <div class="service-item service-item-green">
        <img src="/assets/images/content/icon-bin-green.png" alt="Green Bin">
        <h3>Green bin</h3>
        <p>Garden and food waste</p>
        <p>Thursday, 7 May 2026</p>
        <a href="/what-goes-in-green-bin">What goes in your green bin</a>
    </div>
    <div class="service-item service-item-black">
        <img src="/assets/images/content/icon-bin-black.png" alt="Black Bin">
        <h3>Black bin</h3>
        <p>Non-recyclables</p>
        <p>Thursday, 14 May 2026</p>
        <a href="/what-goes-in-black-bin">What goes in your black bin</a>
    </div>
    <div class="service-item service-item-blue">
        <img src="/assets/images/content/icon-bin-blue.png" alt="Blue Bin">
        <h3>Blue bin</h3>
        <p>Paper, cardboard and cartons</p>
        <p>Thursday, 21 May 2026</p>
        <a href="/what-goes-in-blue-bin">What goes in your blue bin</a>
    </div>
    <div class="service-item service-item-brown">
        <img src="/assets/images/content/icon-bin-brown.png" alt="Brown Bin">
        <h3>Brown bin</h3>
        <p>Plastic, glass, tins, cans and aerosols</p>
        <p>Thursday, 21 May 2026</p>
        <a href="/what-goes-in-brown-bin">What goes in your brown bin</a>
    </div>
</body>
</html>
"""

# Alternative HTML structure without the secondary class name
SAMPLE_HTML_SIMPLE_CLASS = """
<!DOCTYPE html>
<html>
<body>
    <div class="service-item">
        <h3>Green bin</h3>
        <p>Garden and food waste</p>
        <p>Thursday, 7 May 2026</p>
    </div>
    <div class="service-item">
        <h3>Black bin</h3>
        <p>Non-recyclables</p>
        <p>Thursday, 14 May 2026</p>
    </div>
</body>
</html>
"""

# HTML with dates in different format (no day name)
SAMPLE_HTML_SHORT_DATE = """
<!DOCTYPE html>
<html>
<body>
    <div class="service-item">
        <h3>Green bin</h3>
        <p>7 May 2026</p>
    </div>
    <div class="service-item">
        <h3>Black bin</h3>
        <p>14 May 2026</p>
    </div>
</body>
</html>
"""


class MockResponse:
    """Mock requests.Response object."""

    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


@pytest.fixture
def source():
    """Create a Source instance for testing."""
    return stockport_gov_uk.Source(uprn="100011501705")


# =============================================================================
# Tests for correct date extraction per bin type
# =============================================================================


def test_each_bin_gets_correct_date(source):
    """Test that each bin type gets its own correct date, not another bin's date.

    This is the key regression test - the old code had a bug where all bins
    would get the same date (the first bin's date) due to incorrect HTML parsing.
    """
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse(SAMPLE_HTML)
        entries = source.fetch()

    # Convert to dict for easier assertion
    entries_by_type = {e.type: e.date for e in entries}

    assert entries_by_type["Green bin"] == date(2026, 5, 7)
    assert entries_by_type["Black bin"] == date(2026, 5, 14)  # NOT May 7!
    assert entries_by_type["Blue bin"] == date(2026, 5, 21)
    assert entries_by_type["Brown bin"] == date(2026, 5, 21)


def test_fetch_returns_all_bins(source):
    """Test that all bin types are returned."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse(SAMPLE_HTML)
        entries = source.fetch()

    assert len(entries) == 4
    bin_types = {e.type for e in entries}
    assert bin_types == {"Green bin", "Blue bin", "Black bin", "Brown bin"}


def test_correct_icons_assigned(source):
    """Test that correct icons are assigned to each bin type."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse(SAMPLE_HTML)
        entries = source.fetch()

    entries_by_type = {e.type: e.icon for e in entries}

    assert entries_by_type["Green bin"] == "mdi:leaf"
    assert entries_by_type["Black bin"] == "mdi:trash-can"
    assert entries_by_type["Blue bin"] == "mdi:recycle"
    assert entries_by_type["Brown bin"] == "mdi:glass-fragile"


# =============================================================================
# Tests for HTML structure variations
# =============================================================================


def test_simple_class_structure(source):
    """Test parsing works with simplified class names (just 'service-item')."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse(SAMPLE_HTML_SIMPLE_CLASS)
        entries = source.fetch()

    assert len(entries) == 2
    entries_by_type = {e.type: e.date for e in entries}
    assert entries_by_type["Green bin"] == date(2026, 5, 7)
    assert entries_by_type["Black bin"] == date(2026, 5, 14)


def test_short_date_format(source):
    """Test parsing works with dates without day names (e.g., '7 May 2026')."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse(SAMPLE_HTML_SHORT_DATE)
        entries = source.fetch()

    assert len(entries) == 2
    entries_by_type = {e.type: e.date for e in entries}
    assert entries_by_type["Green bin"] == date(2026, 5, 7)
    assert entries_by_type["Black bin"] == date(2026, 5, 14)


# =============================================================================
# Tests for edge cases
# =============================================================================


def test_empty_response(source):
    """Test handling of empty HTML response."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse("<html><body></body></html>")
        entries = source.fetch()

    assert entries == []


def test_no_service_items(source):
    """Test handling when no service-item divs are found."""
    html = """
    <html><body>
        <div class="other-class">
            <h3>Green bin</h3>
            <p>Thursday, 7 May 2026</p>
        </div>
    </body></html>
    """
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse(html)
        entries = source.fetch()

    assert entries == []


def test_missing_date_in_section(source):
    """Test handling when a bin section has no date."""
    html = """
    <html><body>
        <div class="service-item">
            <h3>Green bin</h3>
            <p>Garden and food waste</p>
        </div>
        <div class="service-item">
            <h3>Black bin</h3>
            <p>Thursday, 14 May 2026</p>
        </div>
    </body></html>
    """
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse(html)
        entries = source.fetch()

    # Should only return the bin with a valid date
    assert len(entries) == 1
    assert entries[0].type == "Black bin"
    assert entries[0].date == date(2026, 5, 14)


def test_uprn_used_in_url(source):
    """Test that the UPRN is correctly used in the request URL."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse(SAMPLE_HTML)
        source.fetch()

    mock_get.assert_called_once_with(
        "https://myaccount.stockport.gov.uk/bin-collections/show/100011501705"
    )


# =============================================================================
# Tests for bin name normalization
# =============================================================================


def test_uppercase_bin_names():
    """Test that uppercase bin names are normalized correctly."""
    html = """
    <html><body>
        <div class="service-item">
            <h3>BLACK BIN</h3>
            <p>Thursday, 14 May 2026</p>
        </div>
    </body></html>
    """
    source = stockport_gov_uk.Source(uprn="test")
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse(html)
        entries = source.fetch()

    assert len(entries) == 1
    assert entries[0].type == "Black bin"
    assert entries[0].icon == "mdi:trash-can"


def test_mixed_case_bin_names():
    """Test that mixed case bin names are normalized correctly."""
    html = """
    <html><body>
        <div class="service-item">
            <h3>bLaCk BiN</h3>
            <p>Thursday, 14 May 2026</p>
        </div>
    </body></html>
    """
    source = stockport_gov_uk.Source(uprn="test")
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse(html)
        entries = source.fetch()

    assert len(entries) == 1
    assert entries[0].type == "Black bin"


# =============================================================================
# Tests for descriptions with commas (regression test)
# =============================================================================


def test_descriptions_with_commas():
    """Test that commas in description paragraphs don't break date parsing.

    The old code used string.find(', ') to skip the day name in dates like
    'Thursday, 14 May 2026'. If a description paragraph contained a comma
    (e.g., 'Garden, food and organic waste'), the old code would incorrectly
    try to parse the text after that comma as a date.
    """
    html = """
    <html><body>
        <div class="service-item">
            <h3>Green bin</h3>
            <p>Garden, food and organic waste</p>
            <p>Thursday, 7 May 2026</p>
        </div>
        <div class="service-item">
            <h3>Black bin</h3>
            <p>Non-recyclables, general waste</p>
            <p>Thursday, 14 May 2026</p>
        </div>
        <div class="service-item">
            <h3>Blue bin</h3>
            <p>Paper, cardboard, and cartons</p>
            <p>Thursday, 21 May 2026</p>
        </div>
    </body></html>
    """
    source = stockport_gov_uk.Source(uprn="test")
    with patch("requests.get") as mock_get:
        mock_get.return_value = MockResponse(html)
        entries = source.fetch()

    assert len(entries) == 3
    entries_by_type = {e.type: e.date for e in entries}
    assert entries_by_type["Green bin"] == date(2026, 5, 7)
    assert entries_by_type["Black bin"] == date(2026, 5, 14)
    assert entries_by_type["Blue bin"] == date(2026, 5, 21)
