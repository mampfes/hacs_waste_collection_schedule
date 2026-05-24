"""
Unit tests for London Borough of Hillingdon waste collection source.

Note: This test file is not auto-discovered by pytest due to pytest.ini configuration
(python_files = test_source_components.py). Run it explicitly:

    pytest tests/test_hillingdon_gov_uk.py
    pytest tests/test_hillingdon_gov_uk.py -v
"""

import os
import sys
from datetime import date as real_date
from datetime import timedelta
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

from waste_collection_schedule import Icons  # noqa: E402
from waste_collection_schedule.exceptions import SourceArgumentNotFound  # noqa: E402
from waste_collection_schedule.source import hillingdon_gov_uk  # noqa: E402

# ---------------------------------------------------------------------------
# Shared fixtures and helpers
# ---------------------------------------------------------------------------

# 2026-06-01 is a Monday; used to pin date.today() for deterministic tests.
FROZEN_MONDAY = real_date(2026, 6, 1)
# 2026-05-27 is a Wednesday.
FROZEN_WEDNESDAY = real_date(2026, 5, 27)


def _api_response(collection_day="Monday", collection=None, success=True):
    """Build a minimal Hillingdon JSON-RPC API response dict."""
    if collection is None:
        collection = ["Dry mixed recycling", "Household waste"]
    return {
        "jsonrpc": "2.0",
        "id": "1",
        "result": {
            "success": success,
            "collection": collection,
            "collectionDay": collection_day,
            "gardenWasteCollectionDate": "",
        },
    }


BANK_HOLIDAY_HTML = """
<html><body>
<table>
  <tr><th>Normal Day</th><th>Revised Day</th></tr>
  <tr><td>Monday 25 May (Bank Holiday)</td><td>Tuesday 26 May</td></tr>
  <tr><td>Tuesday 26 May</td><td>Wednesday 27 May</td></tr>
</table>
</body></html>
"""

BANK_HOLIDAY_HTML_NO_TABLE = "<html><body><p>No table here.</p></body></html>"

BANK_HOLIDAY_HTML_MALFORMED = """
<html><body>
<table>
  <tr><th>Normal Day</th><th>Revised Day</th></tr>
  <tr><td>Not a date at all</td><td>Also not a date</td></tr>
  <tr><td>Monday 25 May (Bank Holiday)</td><td>Tuesday 26 May</td></tr>
</table>
</body></html>
"""


class MockResponse:
    """Minimal requests.Response stand-in."""

    def __init__(self, json_data=None, text="", status_code=200):
        self._json = json_data
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            from requests import HTTPError

            raise HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


# ---------------------------------------------------------------------------
# Section 1: _strip_suffix (pure function)
# ---------------------------------------------------------------------------


def test_strip_suffix_removes_expiry():
    result = hillingdon_gov_uk._strip_suffix("Garden Waste ( - 31/05/2026 23:59)")
    assert result == "Garden Waste"


def test_strip_suffix_no_op_on_clean_name():
    assert hillingdon_gov_uk._strip_suffix("Dry mixed recycling") == "Dry mixed recycling"


def test_strip_suffix_handles_empty_parenthetical():
    assert hillingdon_gov_uk._strip_suffix("Waste ( - )") == "Waste"


def test_strip_suffix_preserves_name_with_no_suffix():
    assert hillingdon_gov_uk._strip_suffix("Food waste") == "Food waste"


def test_strip_suffix_strips_trailing_whitespace():
    result = hillingdon_gov_uk._strip_suffix("Household waste  ( - 01/01/2027 00:00)  ")
    assert result == "Household waste"


# ---------------------------------------------------------------------------
# Section 2: _get_icon (pure function)
# ---------------------------------------------------------------------------


def test_get_icon_recycling():
    assert hillingdon_gov_uk._get_icon("Dry mixed recycling") == Icons.RECYCLING


def test_get_icon_food_waste():
    assert hillingdon_gov_uk._get_icon("Food waste") == Icons.BIO_KITCHEN


def test_get_icon_garden_waste():
    assert hillingdon_gov_uk._get_icon("Garden Waste") == Icons.GARDEN


def test_get_icon_household_waste():
    assert hillingdon_gov_uk._get_icon("Household waste") == Icons.GENERAL_WASTE


def test_get_icon_residual_waste():
    assert hillingdon_gov_uk._get_icon("Residual Household Waste") == Icons.GENERAL_WASTE


def test_get_icon_trade_commercial():
    assert hillingdon_gov_uk._get_icon("Trade Sacks General Waste") == Icons.COMMERCIAL


def test_get_icon_case_insensitive():
    assert hillingdon_gov_uk._get_icon("DRY MIXED RECYCLING") == Icons.RECYCLING
    assert hillingdon_gov_uk._get_icon("FOOD WASTE") == Icons.BIO_KITCHEN


def test_get_icon_unknown_returns_none():
    assert hillingdon_gov_uk._get_icon("Unrecognised Stream") is None


def test_get_icon_returns_icons_enum_member():
    icon = hillingdon_gov_uk._get_icon("Dry mixed recycling")
    assert isinstance(icon, Icons)


# ---------------------------------------------------------------------------
# Section 3: Source.__init__
# ---------------------------------------------------------------------------


def test_init_stores_uprn_as_string():
    s = hillingdon_gov_uk.Source(uprn="100021484628")
    assert s._uprn == "100021484628"


def test_init_coerces_integer_uprn_to_string():
    s = hillingdon_gov_uk.Source(uprn=100021484628)
    assert isinstance(s._uprn, str)
    assert s._uprn == "100021484628"


# ---------------------------------------------------------------------------
# Section 4: Source.fetch() — happy path
# ---------------------------------------------------------------------------


@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_returns_8_dates_per_waste_type(mock_requests, mock_bh):
    """2 waste types × 8 weeks = 16 entries."""
    mock_bh.return_value = {}
    mock_requests.post.return_value = MockResponse(
        json_data=_api_response("Wednesday", ["Dry mixed recycling", "Household waste"])
    )

    entries = hillingdon_gov_uk.Source(uprn="123").fetch()

    assert len(entries) == 16


@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_all_dates_on_correct_weekday(mock_requests, mock_bh):
    """All returned dates must fall on Wednesday when collectionDay is 'Wednesday'."""
    mock_bh.return_value = {}
    mock_requests.post.return_value = MockResponse(
        json_data=_api_response("Wednesday", ["Household waste"])
    )

    entries = hillingdon_gov_uk.Source(uprn="123").fetch()

    assert len(entries) == 8
    for entry in entries:
        assert entry.date.weekday() == 2, (
            f"Expected Wednesday (weekday 2), got {entry.date} (weekday {entry.date.weekday()})"
        )


@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_all_dates_today_or_future(mock_requests, mock_bh):
    """No date returned should be in the past."""
    mock_bh.return_value = {}
    mock_requests.post.return_value = MockResponse(
        json_data=_api_response("Monday", ["Household waste"])
    )

    entries = hillingdon_gov_uk.Source(uprn="123").fetch()

    today = real_date.today()
    for entry in entries:
        assert entry.date >= today, f"Collection date {entry.date} is in the past"


@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_strips_subscription_expiry_suffix(mock_requests, mock_bh):
    """'Garden Waste ( - 31/05/2026 23:59)' should appear as 'Garden Waste'."""
    mock_bh.return_value = {}
    mock_requests.post.return_value = MockResponse(
        json_data=_api_response(
            "Monday",
            ["Garden Waste ( - 31/05/2026 23:59)", "Food waste"],
        )
    )

    entries = hillingdon_gov_uk.Source(uprn="123").fetch()

    waste_types = {e.type for e in entries}
    assert "Garden Waste" in waste_types
    assert not any("( -" in t for t in waste_types), (
        "Raw suffix should have been stripped from waste type"
    )


@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_icons_assigned_correctly(mock_requests, mock_bh):
    """Icons must match the Icons enum for known waste types."""
    mock_bh.return_value = {}
    mock_requests.post.return_value = MockResponse(
        json_data=_api_response(
            "Monday",
            ["Dry mixed recycling", "Household waste", "Garden waste", "Food waste"],
        )
    )

    entries = hillingdon_gov_uk.Source(uprn="123").fetch()

    by_type = {e.type: e.icon for e in entries}
    assert by_type["Dry mixed recycling"] == Icons.RECYCLING
    assert by_type["Household waste"] == Icons.GENERAL_WASTE
    assert by_type["Garden waste"] == Icons.GARDEN
    assert by_type["Food waste"] == Icons.BIO_KITCHEN


@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_posts_correct_uprn_in_payload(mock_requests, mock_bh):
    """The UPRN must appear in the JSON-RPC params as the string 'UPRN' key."""
    mock_bh.return_value = {}
    mock_requests.post.return_value = MockResponse(
        json_data=_api_response("Monday", ["Household waste"])
    )

    hillingdon_gov_uk.Source(uprn="999888777").fetch()

    call_kwargs = mock_requests.post.call_args
    payload = call_kwargs[1]["json"]
    assert payload["params"]["UPRN"] == "999888777"
    assert payload["method"] == "Hillingdon.DatasourceQueries.alloy.GetBinCollectionDay"


@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_dates_span_roughly_two_months(mock_requests, mock_bh):
    """8 weekly dates should span exactly 7 weeks from the first date."""
    mock_bh.return_value = {}
    mock_requests.post.return_value = MockResponse(
        json_data=_api_response("Thursday", ["Household waste"])
    )

    entries = hillingdon_gov_uk.Source(uprn="123").fetch()
    dates = sorted({e.date for e in entries})

    assert len(dates) == 8
    assert dates[-1] - dates[0] == timedelta(weeks=7)


# ---------------------------------------------------------------------------
# Section 5: Source.fetch() — bank holiday substitution
# ---------------------------------------------------------------------------


@patch("waste_collection_schedule.source.hillingdon_gov_uk.date")
@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_applies_bank_holiday_substitution(mock_requests, mock_bh, mock_date):
    """When the first collection day falls on a bank holiday, it should be shifted."""
    # Freeze today to a known Monday
    mock_date.today.return_value = FROZEN_MONDAY  # 2026-06-01 (Monday)

    # Substitute the first Monday → Tuesday
    tuesday = FROZEN_MONDAY + timedelta(days=1)
    mock_bh.return_value = {FROZEN_MONDAY: tuesday}
    mock_requests.post.return_value = MockResponse(
        json_data=_api_response("Monday", ["Household waste"])
    )

    entries = hillingdon_gov_uk.Source(uprn="123").fetch()

    dates = sorted({e.date for e in entries})
    assert FROZEN_MONDAY not in dates, "Bank holiday date should have been substituted"
    assert tuesday in dates, "Revised date should appear in collections"


@patch("waste_collection_schedule.source.hillingdon_gov_uk.date")
@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_only_affected_date_is_substituted(mock_requests, mock_bh, mock_date):
    """Only the specific bank holiday date should shift; the other 7 stay on Monday."""
    mock_date.today.return_value = FROZEN_MONDAY

    tuesday = FROZEN_MONDAY + timedelta(days=1)
    mock_bh.return_value = {FROZEN_MONDAY: tuesday}
    mock_requests.post.return_value = MockResponse(
        json_data=_api_response("Monday", ["Household waste"])
    )

    entries = hillingdon_gov_uk.Source(uprn="123").fetch()

    dates = sorted({e.date for e in entries})
    # 7 of the 8 dates should still be Mondays
    mondays = [d for d in dates if d.weekday() == 0]
    assert len(mondays) == 7
    # The shifted date is a Tuesday
    tuesdays = [d for d in dates if d.weekday() == 1]
    assert len(tuesdays) == 1
    assert tuesdays[0] == tuesday


@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_succeeds_when_bank_holiday_page_unavailable(mock_requests):
    """Network error fetching bank holiday page must not prevent collections returning."""
    mock_requests.post.return_value = MockResponse(
        json_data=_api_response("Wednesday", ["Household waste"])
    )
    mock_requests.get.side_effect = ConnectionError("Network unreachable")

    entries = hillingdon_gov_uk.Source(uprn="123").fetch()

    assert len(entries) == 8
    for entry in entries:
        assert entry.date.weekday() == 2  # Still Wednesdays, no substitution


# ---------------------------------------------------------------------------
# Section 6: Source.fetch() — error handling
# ---------------------------------------------------------------------------


@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_raises_source_not_found_when_api_reports_failure(mock_requests, mock_bh):
    """result.success=false must raise SourceArgumentNotFound, not return []."""
    mock_bh.return_value = {}
    mock_requests.post.return_value = MockResponse(
        json_data={"jsonrpc": "2.0", "id": "1", "result": {"success": False}}
    )

    with pytest.raises(SourceArgumentNotFound) as exc_info:
        hillingdon_gov_uk.Source(uprn="000000000000").fetch()

    assert exc_info.value.argument == "uprn"


@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_raises_source_not_found_for_nobin(mock_requests, mock_bh):
    """'NOBIN' collection day (large commercial bins) must raise SourceArgumentNotFound."""
    mock_bh.return_value = {}
    mock_requests.post.return_value = MockResponse(
        json_data={
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "success": True,
                "collection": ["1100 ltr General Waste"],
                "collectionDay": "NOBIN",
            },
        }
    )

    with pytest.raises(SourceArgumentNotFound) as exc_info:
        hillingdon_gov_uk.Source(uprn="100021484646").fetch()

    assert exc_info.value.argument == "uprn"


@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_raises_source_not_found_for_unknown_day(mock_requests, mock_bh):
    """An unrecognised collectionDay string must raise SourceArgumentNotFound."""
    mock_bh.return_value = {}
    mock_requests.post.return_value = MockResponse(
        json_data={
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "success": True,
                "collection": ["Household waste"],
                "collectionDay": "Someday",
            },
        }
    )

    with pytest.raises(SourceArgumentNotFound):
        hillingdon_gov_uk.Source(uprn="123").fetch()


@patch(
    "waste_collection_schedule.source.hillingdon_gov_uk._fetch_bank_holiday_substitutions"
)
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_fetch_http_error_propagates(mock_requests, mock_bh):
    """An HTTP error from the API must propagate (not be swallowed)."""
    from requests import HTTPError

    mock_bh.return_value = {}
    mock_requests.post.return_value = MockResponse(status_code=503)

    with pytest.raises(HTTPError):
        hillingdon_gov_uk.Source(uprn="123").fetch()


# ---------------------------------------------------------------------------
# Section 7: _fetch_bank_holiday_substitutions
# ---------------------------------------------------------------------------


@patch("waste_collection_schedule.source.hillingdon_gov_uk.date")
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_bank_holiday_parses_table_correctly(mock_requests, mock_date):
    """Should return a dict mapping normal date → revised date for each table row."""
    # Freeze today so year assignment is deterministic
    mock_date.today.return_value = real_date(2026, 5, 20)

    mock_requests.get.return_value = MockResponse(text=BANK_HOLIDAY_HTML)

    result = hillingdon_gov_uk._fetch_bank_holiday_substitutions()

    assert real_date(2026, 5, 25) in result
    assert result[real_date(2026, 5, 25)] == real_date(2026, 5, 26)
    assert real_date(2026, 5, 26) in result
    assert result[real_date(2026, 5, 26)] == real_date(2026, 5, 27)


@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_bank_holiday_returns_empty_on_network_error(mock_requests):
    """A connection error must be silently caught and return an empty dict."""
    mock_requests.get.side_effect = ConnectionError("DNS failure")

    result = hillingdon_gov_uk._fetch_bank_holiday_substitutions()

    assert result == {}


@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_bank_holiday_returns_empty_on_http_error(mock_requests):
    """A 404/500 response must be silently caught and return an empty dict."""
    mock_requests.get.return_value = MockResponse(status_code=404)

    result = hillingdon_gov_uk._fetch_bank_holiday_substitutions()

    assert result == {}


@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_bank_holiday_returns_empty_when_no_table(mock_requests):
    """Page with no <table> element should return an empty dict."""
    mock_requests.get.return_value = MockResponse(text=BANK_HOLIDAY_HTML_NO_TABLE)

    result = hillingdon_gov_uk._fetch_bank_holiday_substitutions()

    assert result == {}


@patch("waste_collection_schedule.source.hillingdon_gov_uk.date")
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_bank_holiday_skips_malformed_rows_parses_valid_ones(mock_requests, mock_date):
    """Rows that cannot be parsed as dates should be silently skipped."""
    mock_date.today.return_value = real_date(2026, 5, 20)
    mock_requests.get.return_value = MockResponse(text=BANK_HOLIDAY_HTML_MALFORMED)

    result = hillingdon_gov_uk._fetch_bank_holiday_substitutions()

    # The malformed row is skipped; the valid row is parsed
    assert real_date(2026, 5, 25) in result
    assert result[real_date(2026, 5, 25)] == real_date(2026, 5, 26)


@patch("waste_collection_schedule.source.hillingdon_gov_uk.date")
@patch("waste_collection_schedule.source.hillingdon_gov_uk.requests")
def test_bank_holiday_assigns_next_year_for_past_dates(mock_requests, mock_date):
    """Dates more than 30 days in the past should roll over to next year."""
    # Freeze today to December — January bank holidays should use next year
    mock_date.today.return_value = real_date(2026, 12, 15)

    html = """
    <html><body>
    <table>
      <tr><td>Monday 5 January (Bank Holiday)</td><td>Tuesday 6 January</td></tr>
    </table>
    </body></html>
    """
    mock_requests.get.return_value = MockResponse(text=html)

    result = hillingdon_gov_uk._fetch_bank_holiday_substitutions()

    # Jan 5 is >30 days before Dec 15, so it should be assigned year 2027
    assert real_date(2027, 1, 5) in result
    assert result[real_date(2027, 1, 5)] == real_date(2027, 1, 6)
