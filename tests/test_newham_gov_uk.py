"""Tests for the newham_gov_uk source.

Newham's bin collection site is HTML only, and three of its behaviours have
caused silent breakage:

* dates are rendered ``dd/mm/yyyy``, which a month-first parser reads as a
  different (and plausible looking) date;
* an unknown property ID returns HTTP 200 with a fully rendered page, so only
  the empty address card distinguishes it from a real address;
* a card can render an empty "Next" while still showing a "Previous" date
  below it.

The markup in the fixtures below is copied from live responses.

This file is not auto-discovered by pytest: pytest.ini restricts python_files to
test_source_components.py and test_fetch_retry.py. Run it explicitly:

    pytest tests/test_newham_gov_uk.py -o python_files=test_newham_gov_uk.py -v
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(
    str(Path(__file__).parents[1] / "custom_components" / "waste_collection_schedule")
)  # isort:skip

from waste_collection_schedule import Icons  # isort:skip
from waste_collection_schedule.exceptions import SourceArgumentNotFound  # isort:skip
from waste_collection_schedule.source import newham_gov_uk  # isort:skip


class Response:
    def __init__(self, html: str):
        self.text = html

    def raise_for_status(self) -> None:
        return None


ADDRESS_CARD = """
<div class="card">
  <div class="card-header">Your Address</div>
  <p class="card-text"> <i class="fas fa-home fa-4x"></i>
    5 <br/> ST GEORGES ROAD <br/> E7 8HU
  </p>
</div>
"""

EMPTY_ADDRESS_CARD = """
<div class="card">
  <div class="card-header">Your Address</div>
  <p class="card-text"> <i class="fas fa-home fa-4x"></i> <br/> <br/> </p>
</div>
"""

GARDEN_CARD = """
<div class="card h-100">
  <div class="card-header">Green and Garden Waste (only available from Mar to Oct)</div>
  <p class="card-text"> <i class="fas fa-tree fa-4x"></i>We collect green and
    garden waste from Newham residents.
  </p>
</div>
"""


def _collection_card(bin_type: str, extra_class: str, next_date: str, prev_date: str):
    """Build a collection card; an empty next_date renders an empty <mark>."""
    next_mark = (
        f"<mark>Thursday</mark>\xa0{next_date}" if next_date else "<mark></mark>\xa0"
    )
    prev_mark = (
        f"<mark>Wednesday</mark>\xa0{prev_date}" if prev_date else "<mark></mark>\xa0"
    )
    return f"""
    <div class="card h-100 {extra_class}">
      <div class="card-header">Your <b>{bin_type}</b> Collection Day</div>
      <p class="card-text">
        <b>Next\xa0</b>{next_mark}<br/>
        <b>Previous\xa0</b>{prev_mark}<br/>
      </p>
    </div>
    """


def _page(*cards: str) -> str:
    return f"<html><body>{''.join(cards)}</body></html>"


FULL_SERVICE_PAGE = _page(
    ADDRESS_CARD,
    _collection_card("Domestic", "", "03/09/2026", "26/08/2026"),
    _collection_card("Recycling", "card-recycling", "03/09/2026", "26/08/2026"),
    _collection_card("Food Waste", "card-food", "03/09/2026", "26/08/2026"),
    GARDEN_CARD,
)

NO_FOOD_SERVICE_PAGE = _page(
    ADDRESS_CARD,
    _collection_card("Domestic", "", "01/09/2026", "24/08/2026"),
    _collection_card("Recycling", "card-recycling", "01/09/2026", "24/08/2026"),
    _collection_card("Food Waste", "card-food", "", ""),
    GARDEN_CARD,
)

# The shape that made "Next\\D*" match the previous collection: an empty "Next"
# followed by a populated "Previous".
STALE_FOOD_PAGE = _page(
    ADDRESS_CARD,
    _collection_card("Domestic", "", "03/09/2026", "26/08/2026"),
    _collection_card("Food Waste", "card-food", "", "26/08/2026"),
)

UNKNOWN_PROPERTY_PAGE = _page(
    EMPTY_ADDRESS_CARD,
    """
    <div class="card h-100">
      <div class="card-header">Your <b>Domestic</b> Collection Day</div>
      <p class="card-text">There are no domestic collection details available
        for this address!</p>
    </div>
    """,
    GARDEN_CARD,
)


def _fetch(html: str, property_id="000046250697"):
    with patch.object(newham_gov_uk.requests, "get", return_value=Response(html)):
        return newham_gov_uk.Source(property=property_id).fetch()


def test_all_three_collection_types_are_returned():
    entries = _fetch(FULL_SERVICE_PAGE)

    assert [e.type for e in entries] == ["Domestic", "Recycling", "Food Waste"]


def test_food_waste_uses_the_food_icon():
    food = [e for e in _fetch(FULL_SERVICE_PAGE) if e.type == "Food Waste"]

    assert len(food) == 1
    assert food[0].icon == Icons.BIO_KITCHEN


def test_dates_are_parsed_day_first():
    """03/09/2026 is 3 September, not 9 March."""
    entries = _fetch(FULL_SERVICE_PAGE)

    assert {e.date for e in entries} == {date(2026, 9, 3)}


def test_address_and_garden_cards_are_skipped():
    assert len(_fetch(FULL_SERVICE_PAGE)) == 3


def test_property_without_food_service_returns_other_types():
    entries = _fetch(NO_FOOD_SERVICE_PAGE)

    assert [e.type for e in entries] == ["Domestic", "Recycling"]
    assert {e.date for e in entries} == {date(2026, 9, 1)}


def test_empty_next_does_not_fall_through_to_previous():
    entries = _fetch(STALE_FOOD_PAGE)

    assert [e.type for e in entries] == ["Domestic"]
    assert date(2026, 8, 26) not in {e.date for e in entries}


def test_unknown_property_raises_rather_than_returning_nothing():
    with pytest.raises(SourceArgumentNotFound) as excinfo:
        _fetch(UNKNOWN_PROPERTY_PAGE, property_id="999999999999")

    assert "property" in str(excinfo.value)


def test_property_id_is_zero_padded():
    assert newham_gov_uk.Source(property=46012509)._property == "000046012509"


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            "Next\xa0Thursday\xa003/09/2026 Previous\xa0Wednesday\xa026/08/2026",
            "03/09/2026",
        ),
        ("Next 03/09/2026", "03/09/2026"),
        ("Next  Previous  ", None),
        ("Next  Previous Wednesday 26/08/2026", None),
        # No day name before the previous date, so "Previous" is the only word
        # between "Next" and a date. Rejected by the negative lookahead alone.
        ("Next\xa0\xa0Previous\xa026/08/2026", None),
    ],
)
def test_next_date_regex_boundaries(text, expected):
    match = newham_gov_uk.NEXT_DATE.search(text)

    assert (match.group(1) if match else None) == expected
