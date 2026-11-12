"""Regression tests for the Mulhouse Alsace Agglomération source."""

import os
import sys
from datetime import date as real_date
from unittest.mock import patch

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

from waste_collection_schedule.source import mulhouse_alsace_fr

RICHWILLER_COMMENT = (
    "Déchets végétaux (maison individuelle avec jardin) uniquement du "
    "15 avril au 04 novembre 2026."
)


def test_parse_vegetal_period_from_provider_comment():
    assert mulhouse_alsace_fr._parse_vegetal_period(RICHWILLER_COMMENT) == (
        real_date(2026, 4, 15),
        real_date(2026, 11, 4),
    )


def test_vegetal_period_repeats_in_following_year():
    period = mulhouse_alsace_fr._parse_vegetal_period(RICHWILLER_COMMENT)

    assert period is not None
    assert mulhouse_alsace_fr._is_in_vegetal_period(real_date(2027, 4, 21), period)
    assert not mulhouse_alsace_fr._is_in_vegetal_period(real_date(2027, 1, 6), period)


class FrozenDate(real_date):
    @classmethod
    def today(cls):
        return cls(2026, 10, 28)


def test_fetch_omits_green_waste_outside_provider_period():
    row = {
        "freq_omr": "1 fois par semaine",
        "jour_omr": "Mercredi",
        "freq_vert": "1 fois par semaine",
        "jour_vert": "Mercredi",
        "comment": RICHWILLER_COMMENT,
    }

    with (
        patch.object(mulhouse_alsace_fr, "date", FrozenDate),
        patch.object(mulhouse_alsace_fr.Source, "_fetch_rows", return_value=[row]),
    ):
        entries = mulhouse_alsace_fr.Source(commune="Richwiller").fetch()

    green_dates = [entry.date for entry in entries if entry.type == "Déchets verts"]
    household_waste_dates = [
        entry.date for entry in entries if entry.type == "Ordures ménagères"
    ]

    assert green_dates == [
        real_date(2026, 10, 28),
        real_date(2026, 11, 4),
        real_date(2027, 4, 21),
    ]
    assert len(household_waste_dates) == mulhouse_alsace_fr.HORIZON_WEEKS
