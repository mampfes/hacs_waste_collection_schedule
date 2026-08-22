"""Offline regression tests for the Eastleigh Borough Council source.

This file is not auto-discovered because pytest.ini limits python_files. Run it
explicitly with ``pytest tests/test_eastleigh_gov_uk.py``.
"""

import _strptime  # noqa: F401  # preload before the integration path is appended
import calendar  # noqa: F401  # preload before the integration path is appended
import sys
import types
from datetime import date
from pathlib import Path


class MockResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        return None


class MockSession:
    response_text = ""

    def __init__(self, **_kwargs):
        pass

    def get(self, *_args, **_kwargs):
        return MockResponse(self.response_text)


# curl_cffi is unavailable in the author sandbox, and transport is outside this
# parser regression, so provide the same minimal module surface as the source.
curl_cffi = types.ModuleType("curl_cffi")
curl_requests = types.ModuleType("curl_cffi.requests")
curl_requests.Session = MockSession  # type: ignore[attr-defined]
curl_cffi.requests = curl_requests  # type: ignore[attr-defined]
sys.modules["curl_cffi"] = curl_cffi
sys.modules["curl_cffi.requests"] = curl_requests

PACKAGE = Path(__file__).parents[1] / "custom_components" / "waste_collection_schedule"
sys.path.append(str(PACKAGE))

from waste_collection_schedule import Icons  # noqa: E402
from waste_collection_schedule.source import eastleigh_gov_uk  # noqa: E402

HTML = """
<dl>
  <dt>Address</dt><dd>14 Example Street</dd>
  <dt>Household Waste Bin</dt><dd>Wed, 12 Aug 2026</dd>
  <dt>Recycling Bin</dt><dd>Wed, 19 Aug 2026</dd>
  <dt>Food Waste Bin</dt><dd>Wed, 12 Aug 2026</dd>
  <dt>Glass Bin</dt><dd>Wed, 26 Aug 2026</dd>
  <dt>Garden Waste Bin</dt><dd>{garden_date}</dd>
</dl>
"""

CLEAN_GARDEN_DATE = '<time datetime="2026-08-12">Wed, 12 Aug 2026</time>'
FORMATTED_GARDEN_DATE = """
      <time datetime="2026-08-12">Wed, 12 Aug 2026</time>
  """


def fetch_snapshot(garden_date):
    MockSession.response_text = HTML.format(garden_date=garden_date)
    entries = eastleigh_gov_uk.Source(uprn="100060326905").fetch()
    return [(entry.date, entry.type, entry.icon) for entry in entries]


def test_date_text_surrounding_whitespace_does_not_change_collections():
    expected = [
        (date(2026, 8, 12), "Household Waste Bin", Icons.GENERAL_WASTE),
        (date(2026, 8, 19), "Recycling Bin", Icons.RECYCLING),
        (date(2026, 8, 12), "Food Waste Bin", Icons.BIO_KITCHEN),
        (date(2026, 8, 26), "Glass Bin", Icons.GLASS),
        (date(2026, 8, 12), "Garden Waste Bin", Icons.GARDEN),
    ]

    clean = fetch_snapshot(CLEAN_GARDEN_DATE)
    formatted = fetch_snapshot(FORMATTED_GARDEN_DATE)

    assert clean == expected
    assert formatted == clean
    assert fetch_snapshot(FORMATTED_GARDEN_DATE) == formatted
