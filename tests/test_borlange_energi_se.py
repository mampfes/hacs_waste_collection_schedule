"""Tests for the borlange_energi_se date parser.

Borlänge Energi's API replaces the usual dated string with relative wording on
the day of a collection ("Tömning idag") and the day before ("Tömning
imorgon"). Those used to reach the date regex, match nothing and raise
ValueError, which failed the whole fetch on every polling interval.
"""

import os
import sys
from datetime import datetime, timedelta

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

from waste_collection_schedule.source.borlange_energi_se import (
    parse_swedish_date,
)


def _midnight():
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


@pytest.mark.parametrize("text", ["Tömning idag", "Tömning i dag", "IDAG"])
def test_today_is_parsed(text):
    assert parse_swedish_date(text) == _midnight()


@pytest.mark.parametrize("text", ["Tömning imorgon", "Tömning i morgon", "IMORGON"])
def test_tomorrow_is_parsed(text):
    assert parse_swedish_date(text) == _midnight() + timedelta(days=1)


@pytest.mark.parametrize(
    "weekday", ["måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag", "söndag"]
)
def test_weekdays_ending_in_dag_are_not_treated_as_relative(weekday):
    """The relative match is anchored on word boundaries, so a weekday name
    must still fall through to the dated branch."""
    result = parse_swedish_date(f"Nästa tömning sker {weekday} den 15 januari")
    assert (result.month, result.day) == (1, 15)


def test_dated_form_still_parses():
    result = parse_swedish_date("Nästa tömning sker torsdag den 15 januari")
    assert (result.month, result.day) == (1, 15)


def test_past_date_rolls_to_next_year():
    now = datetime.now()
    result = parse_swedish_date("tömning den 1 januari")
    assert result.year == (
        now.year if now.month == 1 and now.day == 1 else now.year + 1
    )


@pytest.mark.parametrize(
    "text",
    [
        "om 3 dagar",  # number followed by a word that is not a month
        "5 veckor",
        "ingen tömning planerad",  # no number at all
    ],
)
def test_unparseable_text_raises_value_error(text):
    """A non-month word after the number used to raise KeyError, which callers
    do not expect; it should be a ValueError like the no-match case."""
    with pytest.raises(ValueError):
        parse_swedish_date(text)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
