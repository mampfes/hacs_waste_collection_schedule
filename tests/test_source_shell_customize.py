import os
import sys
from datetime import date

# Make the core library importable as `waste_collection_schedule`.
sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    )
)

# Use the package-level Collection factory so the legacy ``t=`` keyword
# dispatches to a LegacyCollection (the new-style collection.Collection
# requires waste_type=).
from waste_collection_schedule import Collection  # noqa: E402
from waste_collection_schedule.source_shell import (  # noqa: E402
    Customize,
    customize_function,
    filter_function,
    match_customize,
)

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
