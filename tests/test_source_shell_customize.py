import calendar  # noqa: F401 - import stdlib calendar before the package path
import os
import sys
from datetime import date

import pytest

# Make the core library importable as `waste_collection_schedule`.
sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    )
)

import cassette

# Use the package-level Collection factory so the legacy ``t=`` keyword
# dispatches to a LegacyCollection (the new-style collection.Collection
# requires waste_type=).
from waste_collection_schedule import Collection
from waste_collection_schedule.source_shell import (
    Customize,
    SourceShell,
    customize_function,
    filter_function,
    match_customize,
)
from waste_collection_schedule.waste_types import set_display_language

D = date(2024, 1, 1)


def _coll(t: str) -> Collection:
    return Collection(date=D, t=t)


def test_exact_match_takes_precedence_over_wildcard():
    customize = {
        "Sonderabfall *": Customize("Sonderabfall *", alias="Hazardous family"),
        "Sonderabfall Glas": Customize("Sonderabfall Glas", alias="Glass"),
    }
    # Exact key wins even though the glob would also match.
    assert match_customize(customize, "Sonderabfall Glas").alias == "Glass"
    # No exact key -> falls back to the glob.
    assert match_customize(customize, "Sonderabfall Metall").alias == "Hazardous family"


def test_no_match_returns_none():
    customize = {"Restmüll": Customize("Restmüll")}
    assert match_customize(customize, "Bio") is None


def test_plain_key_is_not_treated_as_pattern():
    # A plain (non-glob) key must only match its exact type.
    customize = {"Bio": Customize("Bio", show=False)}
    assert match_customize(customize, "Biotonne") is None


def test_wildcard_matching_is_case_sensitive():
    customize = {"Sonderabfall *": Customize("Sonderabfall *", show=False)}
    assert match_customize(customize, "Sonderabfall Glas") is not None
    assert match_customize(customize, "sonderabfall glas") is None


def test_filter_function_hides_family_via_wildcard():
    customize = {"Sonderabfall *": Customize("Sonderabfall *", show=False)}
    assert filter_function(_coll("Sonderabfall Glas"), customize) is False
    assert filter_function(_coll("Sonderabfall Metall"), customize) is False
    # Unrelated type is unaffected.
    assert filter_function(_coll("Restmüll"), customize) is True


def test_customize_function_applies_alias_and_icon_via_wildcard():
    customize = {
        "Sonderabfall *": Customize(
            "Sonderabfall *", alias="Hazardous", icon="mdi:biohazard"
        )
    }
    entry = customize_function(_coll("Sonderabfall Glas"), customize)
    assert entry.type == "Hazardous"
    assert entry.icon == "mdi:biohazard"


def test_question_mark_and_charclass_patterns():
    customize = {
        "Bin ?": Customize("Bin ?", show=False),
        "Recycling [AB]": Customize("Recycling [AB]", alias="Recycling"),
    }
    assert filter_function(_coll("Bin 1"), customize) is False
    assert filter_function(_coll("Bin 12"), customize) is True  # ? matches one char
    assert match_customize(customize, "Recycling A").alias == "Recycling"
    assert match_customize(customize, "Recycling C") is None


# ---------------------------------------------------------------------------
# #7117 / #6950: customising a pipeline source by the label the user sees.
#
# A pipeline entry carries a canonical WasteType, so it has two names: the
# locale-independent ``WasteType.id`` ("recyclables") and the localised display
# label the sensor shows ("Differenziata" in Italian). ``_customize_keys``
# returns *both*, and it has to: the config flow presents, stores and builds
# sensors from display labels, so every customise key the UI writes is a display
# name and never an id, while the library's own callers and tests key on the id.
#
# Before #6950 the lookup used the id alone, so a customise entry written by the
# UI never matched and an alias silently did nothing, which is what a user
# reported as #7117. #6950 landed the day after v3.0.0-alpha.1 was tagged and so
# has never shipped; nothing guarded it until these tests. Do not "simplify"
# _customize_keys down to one key in either direction.
#
# Driven off the committed junker_app cassette, so there is no live dependency:
# it is a real pipeline source, in Italian, producing exactly the reporter's
# labels.
# ---------------------------------------------------------------------------

_JUNKER_FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "junker_app", "udine.json"
)
_JUNKER_ARGS = {"municipality": "Udine", "area": "Zona 2-4-5-6 - Utenze domestiche"}


@pytest.fixture
def italian_display():
    """Run the test with collection labels localised to Italian, as #7117 was."""
    set_display_language("it")
    try:
        yield
    finally:
        set_display_language("en")


def _junker_labels(customize: dict[str, Customize]) -> set[str]:
    """Replay the Udine cassette through SourceShell and return the labels shown."""
    shell = SourceShell.create("junker_app", customize, _JUNKER_ARGS)
    assert shell is not None
    with cassette.replaying(_JUNKER_FIXTURE):
        assert shell.fetch(), "cassette replay produced no collections"
    return {entry.type for entry in shell._entries}


def test_junker_cassette_shows_the_reporters_italian_labels(italian_display):
    """Guard the premise of the tests below: these are the labels #7117 is about."""
    labels = _junker_labels({})

    # Localised display name of the canonical RECYCLABLES type...
    assert "Differenziata" in labels
    # ...and an unresolved label carried through verbatim as a preserved type.
    assert "Napkins" in labels


def test_alias_keyed_on_the_display_label_applies(italian_display):
    # The exact #7117 scenario: the user sees "Differenziata" and aliases it.
    labels = _junker_labels(
        {"Differenziata": Customize("Differenziata", alias="Plastica e metallo")}
    )

    assert "Plastica e metallo" in labels
    assert "Differenziata" not in labels


def test_alias_keyed_on_the_canonical_id_still_applies(italian_display):
    # The other half of the pair, and the only one that worked before #6950.
    labels = _junker_labels(
        {"recyclables": Customize("recyclables", alias="Plastica e metallo")}
    )

    assert "Plastica e metallo" in labels
    assert "Differenziata" not in labels


def test_a_preserved_type_is_customisable_by_both_of_its_keys(italian_display):
    # A preserved type reaches the same fallback by a different route: the id is
    # "preserved:Napkins" and the display label is the bare "Napkins".
    by_label = _junker_labels({"Napkins": Customize("Napkins", alias="Tovaglioli")})
    by_id = _junker_labels(
        {"preserved:Napkins": Customize("preserved:Napkins", alias="Tovaglioli")}
    )

    assert "Tovaglioli" in by_label
    assert "Napkins" not in by_label
    assert "Tovaglioli" in by_id
    assert "Napkins" not in by_id


def test_hiding_a_type_by_its_display_label_applies(italian_display):
    # filter_function shares the same key lookup, so it has the same exposure.
    labels = _junker_labels({"Differenziata": Customize("Differenziata", show=False)})

    assert "Differenziata" not in labels
    assert "Organico" in labels  # unrelated types are untouched
