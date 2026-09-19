"""Tests for the sjobo_se calendar parser.

The first day of each week carries a week-number label in the same cell
(``<div>v.2</div>`` followed by the day). Reading the cell's text ran the two
together ("v.25" for Monday the 5th), so ``int()`` raised ValueError and the
whole fetch failed for any address with a collection on such a day.
"""

import os
import sys
from datetime import date

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

from unittest.mock import MagicMock, patch

from waste_collection_schedule.source.sjobo_se import Source

HTML = """
<table class="styleMonth">
  <tr><td class="styleMonthName">Januari - 2026</td></tr>
  <tr><td>
    <table><tr>
      <td class="styleDayHit" colspan="2">
        <div style="float:left">v.2</div><div class="styleInteIdag">5</div>
      </td></tr>
      <tr><td class="RST"></td><td class="MAT"></td></tr>
    </table>
  </td>
  <td>
    <table><tr>
      <td class="styleDayHit"><div class="styleInteIdag">13</div></td></tr>
      <tr><td class="RST"></td></tr>
    </table>
  </td></tr>
</table>
"""


def _fetch():
    response = MagicMock(text=HTML)
    with patch("requests.get", return_value=response):
        return Source(address="Gamla torg 10", city="Sjöbo").fetch()


def test_day_cell_with_week_label_is_parsed():
    dates = {(e.date, e.type) for e in _fetch()}
    assert (date(2026, 1, 5), "Restavfall") in dates
    assert (date(2026, 1, 5), "Matavfall") in dates


def test_plain_day_cell_is_parsed():
    assert date(2026, 1, 13) in {e.date for e in _fetch()}
