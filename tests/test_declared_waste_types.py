"""Gate: a source may only return waste types it declares in ``WASTE_TYPES``.

For a pipeline (``BaseSource``) source, ``WASTE_TYPES`` is meant to be the
authoritative, machine-readable list of canonical waste types the source can
emit. The config flow and the docs consume it, so it must be correct. It is not
yet: it is auto-derived (``base_source.__init_subclass__``) from ONLY a
transformer's explicit ``type_value_map``, while a source can also emit a
canonical ``WasteType`` through the shared alias vocabulary (``resolve()``) or
keep an unknown label with ``preserved()``. Two systematic gaps follow:

* a source that resolves aliases it never lists returns canonical types absent
  from its declared set; and
* a source with an empty map falls back to the whole ``ALL_TYPES`` catalogue, so
  it "declares" everything, which is no declaration at all.

This module replays every recorded cassette (offline, deterministic — the same
machinery as ``test_offline_fixtures``) through the source's ``fetch()`` and
asserts that every returned ``waste_type.id`` is one the source declares,
ignoring ``preserved:`` ids (an intentionally kept unknown label). It also flags
the ``ALL_TYPES`` fallback as a non-declaration.

Only new-style pipeline sources (those with ``PARAMS``) are gated; legacy
``fetch()`` sources have no canonical vocabulary to check. Generic-engine
modules (``ics`` and friends in ``BLACK_LIST``) are exempt: they pass provider
titles straight through and have no fixed vocabulary to declare.

Refresh cassettes with ``python tests/record_fixtures.py --all``.
"""

import calendar  # noqa: F401 - import stdlib calendar before the package path
import os
import sys
from collections import defaultdict

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "../custom_components/waste_collection_schedule",
    ),
)
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from importlib import import_module

import cassette
from fixtures_support import discover_fixtures, slug
from waste_collection_schedule.waste_types import ALL_TYPES

from update_docu_links import BLACK_LIST

# Modules documenting a shared engine (ics, static, ...) rather than one
# provider: same BLACK_LIST the structural tests use to exempt these. A generic
# engine passes arbitrary provider titles through and has no canonical
# vocabulary to declare, so it cannot be gated here.
_GENERIC_ENGINE_SOURCES = {g.split("/")[-1].removesuffix(".md") for g in BLACK_LIST}

_ALL_TYPE_IDS = frozenset(wt.id for wt in ALL_TYPES)

_FIXTURES = discover_fixtures()

# ---------------------------------------------------------------------------
# BURN-DOWN ALLOWLIST — debt tracked by issue #6935.
#
# Every module below currently fails this gate. They are skipped so the suite is
# green today, but the allowlist is a debt register, not a permanent exception
# list: each future per-source correction MUST delete its entry, and
# ``test_allowlist_has_no_stale_entries`` fails if a listed module has been
# fixed (or removed) without its entry going too, so the list cannot rot.
#
# The allowlist MUST reach empty before the ``ALL_TYPES`` fallback in
# ``base_source.__init_subclass__`` can be removed: while the ~20 category (b)
# sources below rely on that fallback, removing it would leave them with an
# empty ``WASTE_TYPES`` and break the existing ``test_has_waste_types`` gate.
# Correcting those sources (giving each a real declared vocabulary) and removing
# the fallback are later phases of #6935, out of scope for this enabling gate.
#
# Contents were derived empirically from a full cassette replay, not hand-typed.
# ---------------------------------------------------------------------------

# (a) Sources that return canonical types they never declare: the transformer
# resolves aliases (or preserves-then-canonicalises labels) beyond its explicit
# type_value_map, so the auto-derived WASTE_TYPES is missing those ids. Fixed by
# declaring the full produced vocabulary on each source. Now cleared.
_RETURNS_UNDECLARED_TYPES: set[str] = set()

# (b) Sources whose WASTE_TYPES == the whole ALL_TYPES catalogue, via the
# empty-map fallback. "Declaring everything" is no declaration; fixed by giving
# each a real, specific vocabulary. Now cleared: bmv_at and muellmax_de had their
# provider-specific labels mapped so they resolve to a declared vocabulary.
_DECLARES_ALL_TYPES: set[str] = set()

ALLOWLIST = _RETURNS_UNDECLARED_TYPES | _DECLARES_ALL_TYPES


def _source_class(module_name: str):
    """Return a source module's ``Source`` class, or ``None``."""
    module = import_module(f"waste_collection_schedule.source.{module_name}")
    return getattr(module, "Source", None)


def _is_gated(module_name: str, cls) -> bool:
    """True if the module is a gateable new-style pipeline source.

    Legacy ``fetch()`` sources (no ``PARAMS``) have no canonical vocabulary to
    declare, and generic-engine modules pass arbitrary titles through; neither
    is subject to this gate.
    """
    if cls is None:
        return False
    if not getattr(cls, "PARAMS", None):
        return False
    if module_name in _GENERIC_ENGINE_SOURCES:
        return False
    return True


def _resolve_case(cls, case_slug: str):
    """Map a cassette slug back to its TEST_CASE constructor kwargs."""
    for key, args in cls.TEST_CASES.items():
        if slug(key) == case_slug:
            return args
    return None


def _violations(cls, results):
    """Return ``(uses_all_types_fallback, undeclared_ids)`` for a fetch result.

    ``preserved:`` ids are excluded: the resolver keeps an unmapped label
    verbatim rather than collapsing it, so it is legitimately absent from the
    declared set.
    """
    declared = frozenset(wt.id for wt in getattr(cls, "WASTE_TYPES", []))
    uses_all_types_fallback = declared == _ALL_TYPE_IDS
    returned = {r.waste_type.id for r in results if r.waste_type is not None}
    undeclared = {
        wid for wid in (returned - declared) if not wid.startswith("preserved:")
    }
    return uses_all_types_fallback, undeclared


@pytest.mark.parametrize(
    "module_name,case_slug,path",
    _FIXTURES,
    ids=[f"{m}::{c}" for m, c, _ in _FIXTURES],
)
def test_returned_waste_types_are_declared(module_name, case_slug, path):
    cls = _source_class(module_name)
    if not _is_gated(module_name, cls):
        pytest.skip(f"{module_name}: not a gated new-style pipeline source")
    if module_name in ALLOWLIST:
        pytest.skip(f"{module_name}: known WASTE_TYPES debt (allowlisted, #6935)")

    args = _resolve_case(cls, case_slug)
    assert args is not None, (
        f"cassette {module_name}/{case_slug} has no matching TEST_CASE"
    )

    with cassette.replaying(path):
        results = cls(**args).fetch()

    uses_all_types_fallback, undeclared = _violations(cls, results)
    assert not uses_all_types_fallback, (
        f"{module_name}: WASTE_TYPES equals the whole ALL_TYPES catalogue "
        f"(empty-map fallback), which is not a real declaration — declare the "
        f"specific types this source produces"
    )
    assert not undeclared, (
        f"{module_name}::{case_slug}: returned undeclared waste types: "
        f"{sorted(undeclared)} — add them to WASTE_TYPES"
    )


def test_allowlist_has_no_stale_entries():
    """The burn-down allowlist must not rot: every entry still exists and fails.

    A stale entry is one whose module has been fixed (now passes the gate),
    removed, or is no longer a gated pipeline source. Any such entry must be
    deleted from the allowlist above, so keeping the list honest is enforced.
    """
    fixtures_by_module: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for m, c, p in _FIXTURES:
        fixtures_by_module[m].append((c, p))

    stale: list[str] = []
    for module_name in sorted(ALLOWLIST):
        try:
            cls = _source_class(module_name)
        except Exception as exc:
            stale.append(f"{module_name}: no longer importable ({exc!r})")
            continue
        if not _is_gated(module_name, cls):
            stale.append(f"{module_name}: no longer a gated pipeline source")
            continue
        cases = fixtures_by_module.get(module_name, [])
        if not cases:
            stale.append(f"{module_name}: no cassette to verify the failure against")
            continue

        still_fails = False
        for case_slug, path in cases:
            args = _resolve_case(cls, case_slug)
            if args is None:
                continue
            with cassette.replaying(path):
                results = cls(**args).fetch()
            uses_all_types_fallback, undeclared = _violations(cls, results)
            if uses_all_types_fallback or undeclared:
                still_fails = True
                break
        if not still_fails:
            stale.append(f"{module_name}: now passes the gate — remove from ALLOWLIST")

    assert not stale, (
        "Stale ALLOWLIST entries (#6935 burn-down — delete each):\n" + "\n".join(stale)
    )
