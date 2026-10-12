"""Unit tests for the East Hampshire District Council source.

Run explicitly because pytest.ini only auto-discovers the source-contract tests:

    pytest tests/test_easthants_gov_uk.py
"""

import os
import sys
from datetime import date
from unittest.mock import Mock

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

from waste_collection_schedule import parsers
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.source import easthants_gov_uk

UPRN_PAGE = """
<div role="region" aria-label="Waste and Recycling">
  <div class="atPanelContent"><h4>Bin Calendar</h4><a href="http://maps.easthants.gov.uk/calendars/H1.pdf">H1</a></div>
  <div class="atPanelContent"><h4>Garden Waste Calendar</h4><a href="/calendars/G5.pdf">G5</a></div>
</div>
"""


def test_uprn_calendar_urls_extracts_and_secures_links():
    assert easthants_gov_uk._uprn_calendar_urls(UPRN_PAGE, "1710041123") == {
        "bins": "http://maps.easthants.gov.uk/calendars/H1.pdf",
        "garden": "http://maps.easthants.gov.uk/calendars/G5.pdf",
    }


def test_uprn_calendar_urls_rejects_unknown_property():
    with pytest.raises(SourceArgumentNotFound):
        easthants_gov_uk._uprn_calendar_urls("<html></html>", "invalid")


def test_colour_matches_requires_the_same_colour_space():
    assert easthants_gov_uk._colour_matches((0.1, 0.2, 0.3), (0.1, 0.2, 0.3))
    assert not easthants_gov_uk._colour_matches((0.1, 0.2, 0.3, 0.4), (0.1, 0.2, 0.3))


def _layout(*cells):
    """A one-page layout: a month heading, then (day text, y, colour) cells."""
    fragments = [parsers.PdfTextFragment(0, "OCT 2026", 20.0, 700.0)]
    vectors = []
    for text, y, colour in cells:
        fragments.append(parsers.PdfTextFragment(0, text, 20.0, y))
        vectors.append(parsers.PdfVector(0, 18.0, y - 2, 71.0, y + 10, None, colour))
    return parsers.PdfDocumentLayout("", tuple(fragments), tuple(vectors))


RUBBISH = (0.248, 0.646, 0.209)
RECYCLING = (0.391, 0.389, 0.387)
GLASS = (0.0, 0.46, 0.748)
SUSPENDED = (0.31, 0.98, 0.0, 0.0)


def test_recycling_includes_glass_when_the_calendar_has_no_glass_colour():
    rows = list(
        easthants_gov_uk._calendar_rows(
            _layout(("THU 01", 600.0, RUBBISH), ("THU 08", 580.0, RECYCLING))
        )
    )
    assert rows == [
        (date(2026, 10, 1), "Rubbish"),
        (date(2026, 10, 8), "Recycling"),
        (date(2026, 10, 8), "Glass"),
    ]


def test_recycling_excludes_glass_when_the_calendar_colours_glass_separately():
    rows = list(
        easthants_gov_uk._calendar_rows(
            _layout(("THU 01", 600.0, RECYCLING), ("THU 08", 580.0, GLASS))
        )
    )
    assert rows == [
        (date(2026, 10, 1), "Recycling"),
        (date(2026, 10, 8), "Glass"),
    ]


def test_suspended_dates_are_skipped_and_unknown_colours_fail():
    rows = list(
        easthants_gov_uk._calendar_rows(
            _layout(("THU 01", 600.0, SUSPENDED), ("THU 08", 580.0, RUBBISH))
        )
    )
    assert rows == [(date(2026, 10, 8), "Rubbish")]
    with pytest.raises(Exception, match="could not determine"):
        list(
            easthants_gov_uk._calendar_rows(
                _layout(("THU 01", 600.0, (0.5, 0.5, 0.0)), ("THU 08", 580.0, RUBBISH))
            )
        )


def test_uprn_pick_returns_bin_and_garden_urls():
    urls = easthants_gov_uk._uprn_pick(Mock(text=UPRN_PAGE), uprn=1710041123)
    assert urls == [
        "http://maps.easthants.gov.uk/calendars/H1.pdf",
        "http://maps.easthants.gov.uk/calendars/G5.pdf",
    ]


INDEX_PAGE = """
<a href="/media/1/download">Calendar 1 (Monday)</a>
<a href="/media/2/download">Calendar 2 (Tuesday)</a>
<a href="/media/3/download">G1 (Monday)</a>
"""


def test_manual_pick_resolves_numbers_and_suggests_on_a_miss():
    page = Mock(text=INDEX_PAGE)
    assert easthants_gov_uk._manual_pick(
        page, calendar_number=2, garden_calendar_number=1
    ) == [
        "https://www.easthants.gov.uk/media/2/download",
        "https://www.easthants.gov.uk/media/3/download",
    ]
    assert easthants_gov_uk._manual_pick(
        page, calendar_number=1, garden_calendar_number=None
    ) == ["https://www.easthants.gov.uk/media/1/download"]
    with pytest.raises(SourceArgumentNotFoundWithSuggestions):
        easthants_gov_uk._manual_pick(page, calendar_number=99)
    with pytest.raises(SourceArgumentNotFound):
        easthants_gov_uk._uprn_pick(page, uprn="abc")
