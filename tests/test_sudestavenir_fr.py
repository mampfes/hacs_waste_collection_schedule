"""Regression tests for the Grand Paris Sud Est Avenir source.

This source-specific file is not included by pytest.ini's default discovery.
Run it explicitly:

    python -m pytest tests/test_sudestavenir_fr.py -q
"""

import os
import sys
from datetime import date as real_date
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

from waste_collection_schedule import Icons
from waste_collection_schedule.source import sudestavenir_fr

MIXED_PRECISI = (
    "7 janvier\n"
    "4 février\n"
    "Tous les mercredis après - midi à partir du 4 mars au 9 décembre"
)


def test_parse_precisi_dates_preserves_month_first_format():
    assert sudestavenir_fr._parse_precisi_dates("Janv. : 5 - 19\nFév. : 2", 2026) == [
        real_date(2026, 1, 5),
        real_date(2026, 1, 19),
        real_date(2026, 2, 2),
    ]


def test_parse_precisi_dates_supports_day_first_full_months():
    assert sudestavenir_fr._parse_precisi_dates(MIXED_PRECISI, 2026) == [
        real_date(2026, 1, 7),
        real_date(2026, 2, 4),
    ]


def test_parse_precisi_range_supports_accented_french_text():
    assert sudestavenir_fr._parse_precisi_range(MIXED_PRECISI, 2026) == (
        real_date(2026, 3, 4),
        real_date(2026, 12, 9),
    )


def test_schedule_dates_limits_weekly_rule_to_precision_range():
    dates = sudestavenir_fr._schedule_dates(
        jour="mercredi",
        frequen="HEBDOMADAIRE",
        pairimp="",
        precisi=MIXED_PRECISI,
        start=real_date(2026, 7, 29),
        end=real_date(2027, 7, 29),
    )

    assert len(dates) == 20
    assert dates[0] == real_date(2026, 7, 29)
    assert dates[-1] == real_date(2026, 12, 9)
    assert all(d.weekday() == 2 for d in dates)


def test_schedule_dates_merges_and_deduplicates_explicit_dates():
    dates = sudestavenir_fr._schedule_dates(
        jour="mercredi",
        frequen="HEBDOMADAIRE",
        pairimp="",
        precisi=(
            "4 mars\nTous les mercredis après - midi à partir du 4 mars au 18 mars"
        ),
        start=real_date(2026, 1, 1),
        end=real_date(2026, 12, 31),
    )

    assert dates == [
        real_date(2026, 3, 4),
        real_date(2026, 3, 11),
        real_date(2026, 3, 18),
    ]


def test_schedule_dates_preserves_month_first_precision_only():
    dates = sudestavenir_fr._schedule_dates(
        jour="mercredi",
        frequen="HEBDOMADAIRE",
        pairimp="",
        precisi="Janv. : 5 - 19\nFév. : 2",
        start=real_date(2026, 1, 1),
        end=real_date(2026, 12, 31),
    )

    assert dates == [
        real_date(2026, 1, 5),
        real_date(2026, 1, 19),
        real_date(2026, 2, 2),
    ]


def test_schedule_dates_limits_fortnightly_rule_to_precision_range():
    dates = sudestavenir_fr._schedule_dates(
        jour="mercredi",
        frequen="QUINZAINE",
        pairimp="PAIRE",
        precisi="Tous les mercredis à partir du 4 mars au 9 décembre",
        start=real_date(2026, 3, 1),
        end=real_date(2026, 12, 31),
    )

    assert len(dates) == 21
    assert dates[0] == real_date(2026, 3, 4)
    assert dates[-1] == real_date(2026, 12, 9)
    assert all(d.weekday() == 2 for d in dates)
    assert all(d.isocalendar().week % 2 == 0 for d in dates)


class FrozenDate(real_date):
    @classmethod
    def today(cls):
        return cls(2026, 7, 29)


class MockResponse:
    def __init__(self, *, text="", json_data=None):
        self.text = text
        self._json_data = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


def _candidate(label):
    return {"label": label, "values": [label]}


def test_fetch_emits_green_waste_for_mixed_precision_schedule():
    session = MagicMock()
    session.get.side_effect = [
        MockResponse(text="const bgSessionId = 'test-session';"),
        MockResponse(
            json_data={
                "properties": {
                    "dv_am_pm": "PM",
                    "dv_frequen": "HEBDOMADAIRE",
                    "dv_jour": "mercredi",
                    "dv_pairimp": "",
                    "dv_precisi": MIXED_PRECISI,
                }
            }
        ),
    ]
    session.post.return_value = MockResponse(
        json_data={"features": [{"properties": {"id_auto": 3633837}}]}
    )

    with (
        patch.object(sudestavenir_fr, "date", FrozenDate),
        patch.object(
            sudestavenir_fr.Source,
            "_resolve",
            side_effect=[
                _candidate("Test commune"),
                _candidate("Test street"),
                _candidate("1"),
            ],
        ),
        patch.object(
            sudestavenir_fr.Source,
            "_query_filter",
            return_value=[_candidate("Test street")],
        ),
        patch.object(sudestavenir_fr.requests, "Session", return_value=session),
    ):
        entries = sudestavenir_fr.Source(
            commune="Test commune",
            street="Test street",
            house_number="1",
        ).fetch()

    assert len(entries) == 20
    assert entries[0].date == real_date(2026, 7, 29)
    assert entries[-1].date == real_date(2026, 12, 9)
    assert {entry.type for entry in entries} == {"Déchets végétaux"}
    assert {entry.icon for entry in entries} == {Icons.GARDEN}
    assert {entry.description for entry in entries} == {"Après-midi"}
