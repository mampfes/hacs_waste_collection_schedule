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

import dateutil.parser  # noqa: F401
import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "../custom_components/waste_collection_schedule",
    ),
)

from importlib import import_module  # noqa: E402

import cassette  # noqa: E402
from fixtures_support import (  # noqa: E402
    discover_choice_fixtures,
    discover_fixtures,
    slug,
)
from waste_collection_schedule.collection import Collection  # noqa: E402

_FIXTURES = discover_fixtures()
_CHOICE_FIXTURES = discover_choice_fixtures()


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
