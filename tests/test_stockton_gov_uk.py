"""Unit tests for the Stockton-on-Tees Borough Council source.

Run explicitly because pytest.ini only auto-discovers the source-contract tests:

    pytest tests/test_stockton_gov_uk.py
"""

import base64
import json
import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch

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

from waste_collection_schedule.source import stockton_gov_uk

FORM = "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2"

FORM_PAGE = f"""
<form id="{FORM}_FORM" action="https://www.stockton.gov.uk/bin-collection-days?pageSessionId=x">
  <input name="{FORM}_PAGESESSIONID" value="page">
  <input name="{FORM}_SESSIONID" value="session">
  <input name="{FORM}_NONCE" value="nonce">
</form>
"""


def _bin(kind, title, date_text):
    return f"""
<div class="grid__cell"><div class="myaccount-block__item--{kind}">
  <p class="myaccount-block__title myaccount-block__title--bin">{title}</p>
  <p>Next collection:</p>
  <p class="myaccount-block__date myaccount-block__date--bin">{date_text}</p>
</div></div>"""


def _garden(text):
    return f"""
<div class="grid__cell"><div class="myaccount-block__item--garden">
  <p class="myaccount-block__title myaccount-block__title--bin">Garden Waste</p>
  <p>{text}</p>
</div></div>"""


def _fetch(garden_html):
    details = (
        _bin("waste", "Waste", "Tue 01 December 2026")
        + _bin("recycling", "Recycling", "Tue 01 December 2026")
        + garden_html
    )
    payload = base64.b64encode(
        json.dumps(
            {"_PAGEORDER_": ["P1"], "P1": {"COLLECTIONDETAILS2": details}}
        ).encode()
    ).decode()
    result_page = f'<script>\nvar {FORM}FormData = "{payload}";\n</script>'

    session = MagicMock()
    session.get.return_value = MagicMock(text=FORM_PAGE)
    session.post.return_value = MagicMock(text=result_page)
    with patch.object(stockton_gov_uk.requests, "Session", return_value=session):
        entries = stockton_gov_uk.Source("100110203615").fetch()
    return sorted((e.date, e.type) for e in entries)


def test_garden_waste_in_season_returns_both_dates():
    garden = _garden(
        "Your next collections are: <strong>Tue 02 June 2026</strong> and "
        "<strong>Tue 16 June 2026</strong>."
    )
    assert _fetch(garden) == [
        (date(2026, 6, 2), "Garden Waste"),
        (date(2026, 6, 16), "Garden Waste"),
        (date(2026, 12, 1), "Recycling"),
        (date(2026, 12, 1), "Waste"),
    ]


def test_garden_waste_after_season_end_keeps_other_bins():
    garden = _garden(
        "If you have subscribed to the Garden Waste service your last collection "
        "for the year is: <strong> Tue 17 November 2026</strong>. "
    )
    assert _fetch(garden) == [
        (date(2026, 11, 17), "Garden Waste"),
        (date(2026, 12, 1), "Recycling"),
        (date(2026, 12, 1), "Waste"),
    ]


def test_garden_waste_without_dates_keeps_other_bins():
    garden = """
<div class="grid__cell"><div class="myaccount-block__item--garden">
  <p class="myaccount-block__title myaccount-block__title--bin">Garden Waste</p>
</div></div>"""
    assert _fetch(garden) == [
        (date(2026, 12, 1), "Recycling"),
        (date(2026, 12, 1), "Waste"),
    ]
