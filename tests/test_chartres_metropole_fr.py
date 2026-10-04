"""Corner-case tests for the Chartres Métropole source.

The recorded cassettes under ``tests/fixtures/chartres_metropole_fr`` cover the
HTTP round-trip, but they can only assert that the replay yields *valid*
collections. The date arithmetic the provider's prose implies — ISO-week parity,
the April-November garden window, "Nth weekday of even months" and the
bank-holiday shift — is exercised here instead, with no network access.
"""

import os
import sys
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from bs4 import BeautifulSoup
from freezegun import freeze_time

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "custom_components",
        "waste_collection_schedule",
    ),
)

from waste_collection_schedule import recurrence
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.source import chartres_metropole_fr as cm

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LEVES_PARAGRAPHS = [
    "Ordures ménagères - (secteur bacs) : mardi matin (sortie des déchets : la veille après 19h)",
    "Ordures ménagères - (secteur sacs) : mardi et vendredi (sortie des déchets : la veille après 19h)",
    "Emballages ménagers et papiers (bacs et sacs) : mercredi matin (sortie des déchets : la veille après 19h)",
    "Encombrants : Le 2ème jeudi des mois pairs : jeudi 12 février, jeudi 9 avril, "
    "jeudi 11 juin, jeudi 13 août, jeudi 8 octobre et jeudi 10 décembre 2026 "
    "(sortie des déchets : la veille après 19h).",
    "Déchets végétaux : jeudi (sortie des déchets : la veille après 19h) "
    "uniquement d’avril à fin novembre.",
]

FROZEN_DAY = "2026-10-01"


def _tag(text: str):
    return BeautifulSoup(f"<p>{text}</p>", "html.parser").p


def _schedules(text: str, **params):
    source = cm.Source(commune=params.pop("commune", "Lèves"), **params)
    return list(cm._describe(_tag(text), source))


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def _html(paragraphs):
    body = "".join(f"<p>{p}</p>" for p in paragraphs)
    return f'<html><body><div class="fiche-description my-4">{body}</div></body></html>'


# ---------------------------------------------------------------------------
# Normalisation / validation helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Bailleau-L’Évêque", "bailleau l eveque"),
        ("Ollé", "olle"),
        ("  Chartres   hypercentre  ", "chartres hypercentre"),
        ("Saint-Léger-des-Aubées", "saint leger des aubees"),
    ],
)
def test_normalize(value, expected):
    assert cm._normalize(value) == expected


@pytest.mark.parametrize("value", ["bacs", "bac", "BACS", "bacs "])
def test_coerce_secteur_bacs(value):
    assert cm._coerce_secteur(value) == "bacs"


@pytest.mark.parametrize("value", ["sacs", "sac", "Sacs"])
def test_coerce_secteur_sacs(value):
    assert cm._coerce_secteur(value) == "sacs"


def test_coerce_secteur_rejects_unknown():
    with pytest.raises(SourceArgumentNotFoundWithSuggestions) as exc:
        cm._coerce_secteur("side")
    assert list(exc.value.suggestions) == ["bacs", "sacs"]


def test_weekdays_preserve_order_and_deduplicate():
    assert cm._weekdays("mardi et vendredi matin") == [
        recurrence.WEEKDAYS["mardi"],
        recurrence.WEEKDAYS["vendredi"],
    ]
    assert cm._weekdays("jeudi jeudi") == [recurrence.WEEKDAYS["jeudi"]]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("encombrants : 2eme jeudi des mois pairs", (2, recurrence.WEEKDAYS["jeudi"])),
        (
            "encombrants : 1er vendredi des mois pairs",
            (1, recurrence.WEEKDAYS["vendredi"]),
        ),
        ("encombrants : 4eme mardi des mois pairs", (4, recurrence.WEEKDAYS["mardi"])),
        (
            "encombrants : 3ème vendredi des mois pairs",
            (3, recurrence.WEEKDAYS["vendredi"]),
        ),
    ],
)
def test_encombrants_rule(text, expected):
    assert cm._encombrants_rule(cm._normalize(text)) == expected


def test_encombrants_rule_absent():
    assert cm._encombrants_rule(cm._normalize("mardi 27 janvier 2026")) is None


def test_explicit_dates_share_year():
    body = cm._normalize("mardi 27 janvier et jeudi 9 juillet 2026")
    assert cm._explicit_dates(body, date(2026, 7, 29)) == [
        date(2026, 1, 27),
        date(2026, 7, 9),
    ]


def test_explicit_dates_infer_year():
    body = cm._normalize("jeudi 12 février et jeudi 9 avril")
    assert cm._explicit_dates(body, date(2026, 7, 29)) == [
        date(2027, 2, 12),
        date(2027, 4, 9),
    ]


def test_page_url_accepts_display_name():
    assert cm._page_url("Lèves").endswith("/leves-collecte")


def test_page_url_unknown_commune_raises_with_suggestions():
    with pytest.raises(SourceArgumentNotFoundWithSuggestions) as exc:
        cm._page_url("Nowhere")
    assert "Lèves" in list(exc.value.suggestions)


# ---------------------------------------------------------------------------
# Schedule projection
# ---------------------------------------------------------------------------


@freeze_time(FROZEN_DAY)
def test_describe_household_weekly_single_sector():
    schedules = _schedules("Ordures ménagères : lundi matin (sortie des déchets)")
    assert len(schedules) == 1
    schedule = schedules[0]
    assert schedule.key == cm.GENERAL_KEY
    assert schedule.iso_week_parity is None
    assert schedule.start == date(2026, 10, 5)  # the next Monday


@freeze_time(FROZEN_DAY)
def test_describe_household_dual_sector_labels():
    schedules = _schedules(LEVES_PARAGRAPHS[0])
    schedules += _schedules(LEVES_PARAGRAPHS[1])
    keys = {s.key for s in schedules}
    assert keys == {"Ordures ménagères (bacs)", "Ordures ménagères (sacs)"}


@freeze_time(FROZEN_DAY)
def test_describe_secteur_filter():
    schedules = _schedules(LEVES_PARAGRAPHS[0], secteur="sacs")
    schedules += _schedules(LEVES_PARAGRAPHS[1], secteur="sacs")
    keys = {s.key for s in schedules}
    assert keys == {"Ordures ménagères (sacs)"}


@freeze_time(FROZEN_DAY)
def test_describe_container_household_waste_skipped():
    assert _schedules("Ordures ménagères : dépôt en conteneur") == []


@freeze_time(FROZEN_DAY)
def test_describe_packaging_even_week():
    schedules = _schedules(
        "Emballages ménagers et papiers : vendredi après-midi - semaine paire "
        "(sortie des déchets : avant 13h)"
    )
    assert schedules[0].iso_week_parity == "even"


@freeze_time(FROZEN_DAY)
def test_describe_packaging_odd_week():
    schedules = _schedules(
        "Emballages ménagers et papiers : mardi après-midi - semaine impaire "
        "(sortie des déchets : avant 13h)"
    )
    assert schedules[0].iso_week_parity == "odd"


@freeze_time(FROZEN_DAY)
def test_describe_garden_window_is_april_to_november():
    schedules = _schedules(
        "Déchets végétaux : jeudi (sortie des déchets : la veille après 19h) "
        "uniquement d’avril à fin novembre."
    )
    assert schedules
    for schedule in schedules:
        assert schedule.step == recurrence.WEEKLY
        assert schedule.start.weekday() == recurrence.WEEKDAYS["jeudi"]
        # The window never leaves April-November; the 26-week horizon may cap it.
        assert 4 <= schedule.not_before.month <= 11
        assert 4 <= schedule.until.month <= 11
        assert schedule.not_before <= schedule.until


@freeze_time(FROZEN_DAY)
def test_describe_garden_point_apport_skipped():
    assert (
        _schedules(
            "Déchets végétaux : dépôt en point d'apport volontaire uniquement "
            "d'avril à fin novembre ."
        )
        == []
    )


@freeze_time(FROZEN_DAY)
def test_describe_encombrants_rule_is_even_months_only():
    schedules = _schedules(
        "Encombrants : Le 2ème jeudi des mois pairs (sortie des déchets : la veille "
        "après 19h)."
    )
    assert len(schedules) == 1
    extra = schedules[0].extra
    assert extra
    assert all(d.month in {2, 4, 6, 8, 10, 12} for d in extra)
    assert all(d.weekday() == recurrence.WEEKDAYS["jeudi"] for d in extra)


@freeze_time(FROZEN_DAY)
def test_describe_encombrants_explicit_dates_only():
    schedules = _schedules(
        "Encombrants : mardi 1 décembre 2026 (sortie des déchets : la veille)"
    )
    assert schedules[0].extra == (date(2026, 12, 1),)


# ---------------------------------------------------------------------------
# Bank-holiday shift
# ---------------------------------------------------------------------------


def _adjust(day: date, key: str = cm.GENERAL_KEY) -> date | None:
    return cm._adjust(day, key, SimpleNamespace())


def test_adjust_normal_week_unchanged():
    assert _adjust(date(2026, 7, 7)) == date(2026, 7, 7)
    assert _adjust(date(2026, 7, 10)) == date(2026, 7, 10)


def test_adjust_holiday_on_collection_day():
    # 2026-11-11 is a Wednesday (Armistice).
    assert _adjust(date(2026, 11, 11)) == date(2026, 11, 12)


def test_adjust_collection_after_holiday_in_same_week():
    assert _adjust(date(2026, 11, 12)) == date(2026, 11, 13)
    assert _adjust(date(2026, 11, 13)) == date(2026, 11, 14)


def test_adjust_collection_before_holiday_is_untouched():
    # Tuesday 2026-11-10 precedes the 11th holiday in the same week.
    assert _adjust(date(2026, 11, 10)) == date(2026, 11, 10)


def test_adjust_monday_holiday_moves_whole_working_week():
    # Lundi de Pâques 2026-04-06.
    assert _adjust(date(2026, 4, 7)) == date(2026, 4, 8)
    assert _adjust(date(2026, 4, 8)) == date(2026, 4, 9)
    assert _adjust(date(2026, 4, 9)) == date(2026, 4, 10)
    assert _adjust(date(2026, 4, 10)) == date(2026, 4, 11)


def test_adjust_friday_holiday_only_moves_that_day():
    # Fête du Travail 2026-05-01 (Friday).
    assert _adjust(date(2026, 4, 30)) == date(2026, 4, 30)
    assert _adjust(date(2026, 5, 1)) == date(2026, 5, 2)


def test_adjust_ascension_thursday():
    assert _adjust(date(2026, 5, 13)) == date(2026, 5, 13)
    assert _adjust(date(2026, 5, 14)) == date(2026, 5, 15)
    assert _adjust(date(2026, 5, 15)) == date(2026, 5, 16)


def test_adjust_weekend_holiday_does_not_move_weekday_collection():
    # Assomption 2026-08-15 (Saturday) and Toussaint 2026-11-01 (Sunday).
    assert _adjust(date(2026, 8, 14)) == date(2026, 8, 14)
    assert _adjust(date(2026, 8, 17)) == date(2026, 8, 17)
    assert _adjust(date(2026, 10, 30)) == date(2026, 10, 30)


def test_adjust_across_year_boundary():
    # 2027-01-01 (Friday) is in the ISO week starting 2026-12-28.
    assert _adjust(date(2027, 1, 1)) == date(2027, 1, 2)


def test_adjust_bulky_waste_is_never_shifted():
    # 2nd Thursday of April 2026 is 2026-04-09, inside the Easter week.
    assert _adjust(date(2026, 4, 9), key=cm.BULKY_KEY) == date(2026, 4, 9)


# ---------------------------------------------------------------------------
# End-to-end pipeline (mocked transport)
# ---------------------------------------------------------------------------


@freeze_time(FROZEN_DAY)
def test_fetch_honours_bank_holidays_and_parity():
    session = MagicMock()
    session.get.return_value = FakeResponse(_html(LEVES_PARAGRAPHS))
    with patch.object(
        cm.Source, "session", new_callable=PropertyMock, return_value=session
    ):
        entries = cm.Source(commune="Lèves").fetch()

    dates_by_type: dict[str, set[date]] = {}
    for entry in entries:
        dates_by_type.setdefault(entry.type, set()).add(entry.date)

    # Tuesday household waste precedes the 11 Nov holiday in the same week.
    assert date(2026, 11, 10) in dates_by_type["General Waste"]
    # Wednesday packaging -> Thursday.
    assert date(2026, 11, 12) in dates_by_type["Recycling"]
    assert date(2026, 11, 11) not in dates_by_type["Recycling"]
    # Thursday garden waste -> Friday.
    assert date(2026, 11, 13) in dates_by_type["Garden Waste"]
    # 2nd Thursday of even months is not shifted.
    assert date(2026, 12, 10) in dates_by_type["Bulky Waste"]


@freeze_time(FROZEN_DAY)
def test_fetch_rejects_unknown_commune_without_network():
    session = MagicMock()
    with patch.object(
        cm.Source, "session", new_callable=PropertyMock, return_value=session
    ):
        with pytest.raises(SourceArgumentNotFoundWithSuggestions):
            cm.Source(commune="Nowhere").fetch()
    session.get.assert_not_called()
