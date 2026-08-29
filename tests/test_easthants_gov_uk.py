"""Unit tests for the East Hampshire District Council source.

Run explicitly because pytest.ini only auto-discovers the source-contract tests:

    pytest tests/test_easthants_gov_uk.py
"""

import os
import sys
from datetime import date
from unittest.mock import Mock, call, patch

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

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
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
        "bins": "https://maps.easthants.gov.uk/calendars/H1.pdf",
        "garden": "https://maps.easthants.gov.uk/calendars/G5.pdf",
    }


def test_uprn_calendar_urls_rejects_unknown_property():
    with pytest.raises(SourceArgumentNotFound):
        easthants_gov_uk._uprn_calendar_urls("<html></html>", "invalid")


def test_colour_matches_requires_the_same_colour_space():
    assert easthants_gov_uk._colour_matches((0.1, 0.2, 0.3), (0.1, 0.2, 0.3))
    assert not easthants_gov_uk._colour_matches((0.1, 0.2, 0.3, 0.4), (0.1, 0.2, 0.3))


def test_waste_types_splits_combined_recycling_and_glass():
    assert easthants_gov_uk._waste_types("recycling", separate_glass=False) == (
        "Recycling",
        "Glass",
    )
    assert easthants_gov_uk._waste_types("recycling", separate_glass=True) == (
        "Recycling",
    )
    assert easthants_gov_uk._waste_types("glass", separate_glass=True) == ("Glass",)


def test_source_requires_uprn_or_calendar_number():
    with pytest.raises(SourceArgumentRequired):
        easthants_gov_uk.Source()


@patch.object(easthants_gov_uk.Source, "_fetch_calendar")
@patch.object(easthants_gov_uk.requests, "Session")
def test_fetch_uses_calendars_assigned_to_uprn(session_factory, fetch_calendar):
    session = session_factory.return_value
    session.get.return_value = Mock(text=UPRN_PAGE)
    fetch_calendar.side_effect = [
        [Collection(date(2026, 9, 1), "Rubbish")],
        [Collection(date(2026, 9, 2), "Garden waste")],
    ]

    collections = easthants_gov_uk.Source(uprn=1710041123).fetch()

    session.get.assert_called_once_with(
        easthants_gov_uk._ADDRESS_URL,
        params={"action": "SetAddress", "UniqueId": "1710041123"},
        timeout=30,
    )
    assert fetch_calendar.call_args_list == [
        call(
            session,
            "https://maps.easthants.gov.uk/calendars/H1.pdf",
            "for UPRN 1710041123",
        ),
        call(
            session,
            "https://maps.easthants.gov.uk/calendars/G5.pdf",
            "garden for UPRN 1710041123",
        ),
    ]
    assert [item.type for item in collections] == ["Rubbish", "Garden waste"]
