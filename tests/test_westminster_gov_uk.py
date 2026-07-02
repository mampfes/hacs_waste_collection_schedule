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


def test_parse_days_wraparound_range():
    assert westminster_gov_uk._parse_days("Fri-Mon") == {0, 4, 5, 6}


# ---------------------------------------------------------------------------
# Section 2: _get_icon (pure function)
# ---------------------------------------------------------------------------


def test_get_icon_rubbish():
    assert (
        westminster_gov_uk._get_icon("Residential rubbish and commercial waste")
        == Icons.GENERAL_WASTE
    )


def test_get_icon_food():
    assert (
        westminster_gov_uk._get_icon("Food Recycling Collection") == Icons.BIO_KITCHEN
    )


def test_get_icon_recycling():
    assert westminster_gov_uk._get_icon("Recycling Collection") == Icons.RECYCLING


def test_get_icon_unknown_returns_none():
    assert westminster_gov_uk._get_icon("Some New Service") is None


# ---------------------------------------------------------------------------
# Section 3: _extract_pairs (panel parser)
# ---------------------------------------------------------------------------

# Minimal page mirroring the live structure: a long-street rubbish row using a
# Mon-Fri range + Sat, Sun weekend, two recycling rows, and a street-cleaning
# panel that must be ignored.
FULL_HTML = """
<html><body>
<div id="pnlrubbishcollection">
<table>
<tr><th>Location</th><th>Week Days</th><th>Week Times</th><th>Weekend Days</th><th>Weekend Times</th></tr>
<tr><td>Some St (BOS)</td><td>Mon-Fri</td><td>09:00 - 10:00</td><td>Sat, Sun</td><td>09:00 - 10:00</td></tr>
</table>
</div>
<div id="pnlrecyclingcollections">
<table>
<tr><th>Location</th><th>Service Description</th><th>Week Days</th><th>Week Times</th><th>Weekend Days</th><th>Weekend Times</th></tr>
<tr><td>Some St</td><td>Food Recycling Collection</td><td>Tue</td><td>08:00 - 14:00</td><td>&nbsp;</td><td>&nbsp;</td></tr>
<tr><td>Some St (part)</td><td>Recycling Collection</td><td>Tue, Fri</td><td>08:00 - 14:00</td><td>&nbsp;</td><td>&nbsp;</td></tr>
</table>
</div>
<div id="pnlstreetcleaning">
<table>
<tr><th>Location</th><th>Service Description</th><th>Week Days</th><th>Weekend Days</th></tr>
<tr><td>Some St</td><td>Your street will be swept on…</td><td>Mon - Fri</td><td>Sat, Sun</td></tr>
</table>
</div>
</body></html>
"""

# A page for a USRN with no collections: panels present but no data rows.
EMPTY_HTML = """
<html><body>
<div id="pnlrubbishcollection"><table>
<tr><th>Location</th><th>Week Days</th><th>Week Times</th><th>Weekend Days</th><th>Weekend Times</th></tr>
</table></div>
<div id="pnlrecyclingcollections"><table>
<tr><th>Location</th><th>Service Description</th><th>Week Days</th><th>Week Times</th><th>Weekend Days</th><th>Weekend Times</th></tr>
</table></div>
</body></html>
"""


def _pairs(html):
    from bs4 import BeautifulSoup

    return westminster_gov_uk._extract_pairs(BeautifulSoup(html, "html.parser"))


def test_extract_pairs_rubbish_all_seven_days():
    pairs = _pairs(FULL_HTML)
    for weekday in range(7):
        assert (westminster_gov_uk.RUBBISH_TYPE, weekday) in pairs


def test_extract_pairs_recycling_types():
    pairs = _pairs(FULL_HTML)
    assert ("Food Recycling Collection", 1) in pairs
    assert ("Recycling Collection", 1) in pairs
    assert ("Recycling Collection", 4) in pairs


def test_extract_pairs_total_count():
    # 7 rubbish + 1 food + 2 recycling = 10 deduped pairs
    assert len(_pairs(FULL_HTML)) == 10


def test_extract_pairs_skips_street_cleaning():
    pairs = _pairs(FULL_HTML)
    assert not any("swept" in t.lower() for t, _ in pairs)


def test_extract_pairs_empty_page_yields_no_pairs():
    assert _pairs(EMPTY_HTML) == set()


# A recycling row missing its leading Location cell (e.g. a merged/omitted
# cell) has one fewer <td> than the header. This must be skipped rather than
# silently reading each subsequent column shifted by one position.
SHIFTED_ROW_HTML = """
<html><body>
<div id="pnlrecyclingcollections">
<table>
<tr><th>Location</th><th>Service Description</th><th>Week Days</th><th>Week Times</th><th>Weekend Days</th><th>Weekend Times</th></tr>
<tr><td>Recycling Collection</td><td>Wed</td><td>Thu</td><td>&nbsp;</td><td>&nbsp;</td></tr>
</table>
</div>
</body></html>
"""


def test_extract_pairs_skips_row_with_mismatched_cell_count():
    assert _pairs(SHIFTED_ROW_HTML) == set()
