"""Offline replay of recorded source cassettes (no network, deterministic).

For every cassette under ``tests/fixtures/`` this replays the recorded HTTP
through the source's full ``fetch()`` pipeline (clock frozen to the recording
date) and checks it yields valid Collections. This is the offline counterpart
to the ``live`` TestNewStyleSourceTestCases: it exercises retrieve/parse/
transform in CI without touching a provider. Refresh with
``python tests/record_fixtures.py --all``.
"""

import calendar  # noqa: F401 - import stdlib calendar before the package path
import datetime
import json
import os
import sys
from collections import Counter
from itertools import pairwise

import dateutil.parser  # noqa: F401
import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "../custom_components/waste_collection_schedule",
    ),
)

from importlib import import_module

import cassette
from fixtures_support import (
    discover_choice_fixtures,
    discover_fixtures,
    fixture_path,
    slug,
)
from waste_collection_schedule.collection import Collection

_FIXTURES = discover_fixtures()
_CHOICE_FIXTURES = discover_choice_fixtures()

# --------------------------------------------------------------------------
# The #7102 debt: how much of what a source sends is actually pinned.
#
# A recorded interaction now stores the request body, and replay refuses a
# request that does not match it. Cassettes recorded before that have no body
# field and are matched on method and URL alone, which pins nothing about the
# payload: a refactor can change what is sent and still replay green, and where
# several requests share a URL the fallback pairs them by position, so a changed
# body can be handed the response recorded for a different request.
#
# They are left that way deliberately. The fix is additive because seven
# pipeline sources cannot be recorded from this location at all (#7051, #7052,
# #7055, #7056, #7095), and a fix that forced a re-record would strand them.
#
# Two gates hold the remainder, because one number cannot do both jobs.
# --------------------------------------------------------------------------

# 1. The ratchet. Every recorded interaction with no stored body is a request
#    that cannot be pinned, whatever happens at replay time. It is a static
#    property of the committed fixtures, so it is exactly reproducible, and
#    re-recording a source is the only thing that moves it. Lower it every time
#    you re-record: that is how the debt gets paid off.
UNPINNED_INTERACTIONS = 2320

# 2. The ceiling. How many requests a full replay may serve off the loose
#    method+url fallback rather than the exact key. This catches what the
#    static count cannot: a cassette that does carry bodies but still falls
#    back, which is what a request-building regression looks like.
#
#    Unlike the ratchet this figure is not exactly reproducible. Measured
#    repeatedly over the full tree it lands between 338 and 341, because two
#    sources do not issue identical requests twice: app_abfallplus_de puts a
#    fresh uuid4 in its POST body (AppAbfallplusDe._client), and lobbe_app
#    varies by one on three cassettes. Nine cassettes are involved, so the
#    ceiling carries a margin of that order and no more. Never raise it for any
#    other reason: a refactor that unpins a source adds far more than nine.
FALLBACK_BUDGET = 350

# Cassettes this run replayed to completion. The ceiling is only meaningful over
# a full pass, so a filtered run (``-k``) or one with a failing replay skips it
# rather than reporting a number that means nothing.
_COMPLETED: set[str] = set()


def _resolve_case(module_name: str, case_slug: str):
    """Map a cassette back to its (Source class, TEST_CASE args)."""
    module = import_module(f"waste_collection_schedule.source.{module_name}")
    for key, args in module.Source.TEST_CASES.items():
        if slug(key) == case_slug:
            return module.Source, args
    return None, None


@pytest.mark.parametrize(
    "module_name,case_slug,path",
    _FIXTURES,
    ids=[f"{m}::{c}" for m, c, _ in _FIXTURES],
)
def test_offline_replay(module_name, case_slug, path):
    cls, args = _resolve_case(module_name, case_slug)
    assert cls is not None, (
        f"cassette {module_name}/{case_slug} has no matching TEST_CASE"
    )

    with cassette.replaying(path):
        results = cls(**args).fetch()

    assert results, f"{module_name}::{case_slug}: replay produced no collections"
    for r in results:
        assert isinstance(r, Collection)
        assert isinstance(r.date, datetime.date)
        assert r.waste_type is not None
    _COMPLETED.add(os.path.abspath(path))


@pytest.mark.parametrize(
    "case_name,first_dates",
    [
        (
            "Fitzroy Town Hall",
            {
                "general_waste": datetime.date(2026, 8, 5),
                "organic": datetime.date(2026, 8, 5),
                "recyclables": datetime.date(2026, 8, 12),
                "glass": datetime.date(2026, 8, 12),
            },
        ),
        (
            "Richmond Town Hall",
            {
                "general_waste": datetime.date(2026, 8, 4),
                "organic": datetime.date(2026, 8, 4),
                "recyclables": datetime.date(2026, 8, 11),
                "glass": datetime.date(2026, 8, 11),
            },
        ),
    ],
)
def test_yarra_replay_preserves_types_dates_and_cadence(case_name, first_dates):
    """Yarra cassettes pin the schedule contract, not merely a non-empty result."""
    module = import_module("waste_collection_schedule.source.yarracity_vic_gov_au")
    path = fixture_path("yarracity_vic_gov_au", case_name)

    with cassette.replaying(path):
        results = module.Source(**module.Source.TEST_CASES[case_name]).fetch()

    expected_counts = {
        "general_waste": 52,
        "organic": 52,
        "recyclables": 26,
        "glass": 13,
    }
    assert len(results) == 143
    assert Counter(result.waste_type.id for result in results) == expected_counts

    expected_cadence = {
        "general_waste": datetime.timedelta(days=7),
        "organic": datetime.timedelta(days=7),
        "recyclables": datetime.timedelta(days=14),
        "glass": datetime.timedelta(days=28),
    }
    for waste_type, first_date in first_dates.items():
        dates = sorted(
            result.date for result in results if result.waste_type.id == waste_type
        )
        assert dates[0] == first_date
        assert all(
            later - earlier == expected_cadence[waste_type]
            for earlier, later in pairwise(dates)
        )


@pytest.mark.parametrize(
    "module_name,path",
    _CHOICE_FIXTURES,
    ids=[m for m, _ in _CHOICE_FIXTURES],
)
def test_offline_choices(module_name, path):
    """Replay a dependent_select source's get_parent_choices/get_choices.

    Exercises the dependent_select config-flow contract offline: the recorded
    HTTP is served back while we call the source's choice methods, asserting the
    parent list includes the recorded parent and the child list includes the
    recorded child. This is what the config flow consumes to populate the
    cascading dropdowns.
    """
    with open(path, encoding="utf-8") as fh:
        meta = json.load(fh)
    module = import_module(f"waste_collection_schedule.source.{module_name}")
    cls = module.Source

    if meta.get("widget") == "cascading_select":
        _replay_cascading_choices(cls, meta, path)
        return

    with cassette.replaying(path):
        if hasattr(cls, "get_parent_choices"):
            parents = cls.get_parent_choices()
            assert isinstance(parents, list) and parents
            assert meta["parent_value"] in parents
        children = cls.get_choices(meta["parent_value"])

    assert isinstance(children, list) and children
    if meta.get("child_value"):
        assert meta["child_value"] in children
    _COMPLETED.add(os.path.abspath(path))


def _replay_cascading_choices(cls, meta, path):
    """Replay an N-level cascading_select get_choices walk.

    For each populated cascade level, asserts get_choices(field, selections)
    returns the expected stored id when it returns any options. A provider may
    not present every level (an auto-fixed level returns []), so empties are
    tolerated, but at least one level must resolve — proving the live walk works.
    """
    fields = meta["fields"]
    expected = meta["expected"]
    any_resolved = False
    with cassette.replaying(path):
        selections = dict(meta["context"])
        for field in fields:
            if field not in expected:
                continue
            choices = cls.get_choices(field, dict(selections))
            assert isinstance(choices, list)
            if choices:
                values = [
                    str(c[1]) if isinstance(c, (list, tuple)) else str(c)
                    for c in choices
                ]
                assert str(expected[field]) in values, (
                    f"{field}: {expected[field]!r} not in {values}"
                )
                any_resolved = True
            selections[field] = expected[field]
    assert any_resolved, "no cascade level resolved any options"
    _COMPLETED.add(os.path.abspath(path))


def test_the_unpinned_interaction_count_only_goes_down():
    """Every recorded interaction that stores no request body is #7102 debt.

    Static, so it costs nothing and is exactly reproducible: it reads the
    committed cassettes and counts. Re-recording a source is the only thing
    that moves it, which is what makes it a ratchet.
    """
    paths = [p for _, _, p in _FIXTURES] + [p for _, p in _CHOICE_FIXTURES]
    unpinned: dict[str, int] = {}
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            interactions = json.load(fh).get("interactions", [])
        missing = sum(1 for it in interactions if "body" not in it)
        if missing:
            unpinned[path] = missing
    total = sum(unpinned.values())

    assert total <= UNPINNED_INTERACTIONS, (
        f"{total} recorded interactions store no request body, up from "
        f"{UNPINNED_INTERACTIONS}. A cassette that does not store what was sent "
        f"cannot tell a refactor from a behaviour change (#7102). Re-record "
        f"with `python tests/record_fixtures.py <module>` rather than raising "
        f"this number."
    )
    assert total == UNPINNED_INTERACTIONS, (
        f"Only {total} recorded interactions now store no request body, down "
        f"from {UNPINNED_INTERACTIONS}. Lower UNPINNED_INTERACTIONS to {total}: "
        f"it is a debt register that ratchets down, and slack in it lets the "
        f"debt grow back unnoticed."
    )


def test_the_replay_fallback_budget_is_not_exceeded():
    """No more requests may go unpinned at replay time than already do (#7102).

    Runs after the replays above and reads the per-cassette counters
    ``cassette.replaying`` leaves behind. Nothing here replays anything itself,
    so the gate costs no extra time.
    """
    paths = [os.path.abspath(p) for _, _, p in _FIXTURES]
    paths += [os.path.abspath(p) for _, p in _CHOICE_FIXTURES]
    if not _COMPLETED.issuperset(paths):
        pytest.skip(
            f"{len(_COMPLETED & set(paths))} of {len(paths)} cassettes replayed "
            "to completion in this run; the fallback ceiling only means anything "
            "over a full pass"
        )

    per_cassette = {p: cassette.REPLAY_FALLBACKS.get(p, 0) for p in paths}
    total = sum(per_cassette.values())
    served = sum(cassette.REPLAY_MATCHES.get(p, 0) for p in paths)
    using = {p: n for p, n in per_cassette.items() if n}
    worst = sorted(((n, p) for p, n in using.items()), reverse=True)[:10]
    detail = "\n".join(f"    {n:>4}  {os.path.relpath(p)}" for n, p in worst)
    summary = (
        f"{total} of {served} replayed requests matched on the loose "
        f"method+url fallback, across {len(using)} of {len(paths)} cassettes."
    )
    print(f"\ncassette fallback debt: {summary}")

    assert total <= FALLBACK_BUDGET, (
        f"{summary}\nThat is above the ceiling of {FALLBACK_BUDGET}. A fallback "
        f"match is a request the cassette does not pin: its body is not "
        f"compared, so a refactor can change what is sent and still replay "
        f"green. Do not raise the ceiling. Re-record the cassette "
        f"(`python tests/record_fixtures.py <module>`) so it carries request "
        f"bodies, or fix whatever stopped the exact key matching.\n"
        f"  worst offenders:\n{detail}"
    )
