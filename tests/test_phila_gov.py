"""Holiday handling of phila_gov for addresses with two trash days (#7828).

In a holiday week the city cancels the secondary trash-only pickup and shifts
the primary trash + recycling pickup. The holiday feed and the AIS address
lookup are replaced with dicts shaped like the real responses, so no network
is used.
"""

import os
import sys
from datetime import date, timedelta

import pytest

sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    )
)

from waste_collection_schedule.source import phila_gov  # isort:skip

YEAR = date.today().year
# Third Monday of February (Presidents' Day), a weekday holiday every year.
HOLIDAY = date(YEAR, 2, 15) + timedelta(days=(7 - date(YEAR, 2, 15).weekday()) % 7)


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def fake_session(props, holiday):
    class FakeSession:
        def get(self, url, headers=None):
            if "trashday" in url:
                return FakeResponse({"holidays": [{"start_date": holiday.isoformat()}]})
            return FakeResponse({"features": [{"properties": props}]})

    return FakeSession


def collections(monkeypatch, props, holiday=HOLIDAY):
    monkeypatch.setattr(phila_gov.requests, "Session", fake_session(props, holiday))
    result: dict[str, set[date]] = {"Rubbish": set(), "Recycle": set()}
    for c in phila_gov.Source("1 Test St").fetch():
        result[c.type].add(c.date)
    return result


def week(start, result):
    return {d for d in result if start <= d < start + timedelta(days=7)}


# Monday holiday comes before the Tuesday secondary, Thursday holiday after it:
# the secondary is cancelled either way.
@pytest.mark.parametrize("holiday", [HOLIDAY, HOLIDAY + timedelta(days=3)])
@pytest.mark.parametrize(
    "props",
    [
        # Secondary listed first: primary/secondary must come from the key name,
        # not from the order of the AIS properties.
        {"secondary_rubbish_day": "TUE", "rubbish_recycle_day": "FRI"},
        {"rubbish_recycle_day": "FRI", "secondary_rubbish_day": "TUE"},
    ],
)
def test_holiday_week_cancels_secondary_and_shifts_primary(monkeypatch, props, holiday):
    result = collections(monkeypatch, props, holiday)

    # Friday primary slips to Saturday, Tuesday secondary is gone.
    assert week(HOLIDAY, result["Rubbish"]) == {HOLIDAY + timedelta(days=5)}
    assert week(HOLIDAY, result["Recycle"]) == {HOLIDAY + timedelta(days=5)}

    # The following, holiday-free week keeps both pickups on their usual days.
    next_monday = HOLIDAY + timedelta(days=7)
    assert week(next_monday, result["Rubbish"]) == {
        next_monday + timedelta(days=1),
        next_monday + timedelta(days=4),
    }
    assert week(next_monday, result["Recycle"]) == {next_monday + timedelta(days=4)}


def test_single_trash_day_still_shifts(monkeypatch):
    result = collections(
        monkeypatch, {"rubbish_recycle_day": "TUE", "secondary_rubbish_day": ""}
    )

    assert week(HOLIDAY, result["Rubbish"]) == {HOLIDAY + timedelta(days=2)}
    assert week(HOLIDAY, result["Recycle"]) == {HOLIDAY + timedelta(days=2)}
