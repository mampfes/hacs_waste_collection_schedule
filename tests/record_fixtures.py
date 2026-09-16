"""Record a source's live HTTP as offline cassettes.

Run manually (never in CI) to capture or refresh cassettes::

    python tests/record_fixtures.py stirling_wa_gov_au [other_module ...]
    python tests/record_fixtures.py --all          # every new-arch source

For each TEST_CASE it runs the full ``fetch()`` once against the live provider,
recording every HTTP interaction (across the curl_cffi and requests stacks) to
``tests/fixtures/<module>/<case_slug>.json`` together with the recording date.
Review the diff and commit; CI then replays those cassettes offline.
"""

import calendar  # noqa: F401 - import stdlib calendar before the package path
import datetime
import glob
import os
import re
import sys

import dateutil.parser  # noqa: F401

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "../custom_components/waste_collection_schedule",
    ),
)

from importlib import import_module

import cassette
from fixtures_support import choices_path, error_fixture_path, fixture_path, slug
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
)

# The family a source is expected to raise for bad input. SourceArgumentExceptionMultiple
# is a sibling of SourceArgumentException rather than a subclass, so it has to be named.
EXPECTED_ERRORS: tuple[type[Exception], ...] = (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
)

SOURCE_DIR = os.path.join(
    os.path.dirname(__file__),
    "../custom_components/waste_collection_schedule/waste_collection_schedule/source",
)


def _new_arch_modules() -> list[str]:
    mods = []
    for path in sorted(glob.glob(os.path.join(SOURCE_DIR, "*.py"))):
        if re.search(
            r"class Source\(BaseSource\)", open(path, encoding="utf-8").read()
        ):
            mods.append(os.path.basename(path)[:-3])
    return mods


def _discard(path: str) -> None:
    """Remove a cassette this run decided not to keep (if one exists)."""
    if os.path.exists(path):
        os.remove(path)


def record(module_name: str) -> None:
    module = import_module(f"waste_collection_schedule.source.{module_name}")
    today = datetime.date.today().isoformat()
    for case_key, args in module.Source.TEST_CASES.items():
        path = fixture_path(module_name, case_key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with cassette.recording(path, today):
                results = module.Source(**args).fetch()
            if not results:
                # An empty fetch makes a useless cassette (provider down or a
                # stale test case); drop it rather than record nothing.
                if os.path.exists(path):
                    os.remove(path)
                print(f"  ! {case_key}: fetch returned no collections, skipped")
                continue
            print(f"  recorded {slug(case_key)} ({len(results)} collections)")
        except Exception as exc:
            print(f"  ! {case_key}: {type(exc).__name__}: {exc}")


def record_errors(module_name: str) -> None:
    """Record a source's ``ERROR_TEST_CASES``: inputs expected to raise.

    Same shape as ``TEST_CASES``, but for arguments an ``ArgumentGuard`` (or
    similar) is expected to reject -- an out-of-area address, say. Only a
    ``SourceArgumentException`` (the family a source is expected to raise for
    bad input, per CLAUDE.md) is recorded; any other exception means the case
    doesn't exercise what it claims to, so it is reported and skipped rather
    than silently pinned.

    A case that fails to record leaves nothing behind: any cassette written by
    this run, and any stale one from an earlier run, is removed, so a case that
    has stopped raising cannot keep replaying green off an old recording.
    """
    module = import_module(f"waste_collection_schedule.source.{module_name}")
    error_cases = getattr(module.Source, "ERROR_TEST_CASES", {})
    today = datetime.date.today().isoformat()
    for case_key, args in error_cases.items():
        path = error_fixture_path(module_name, case_key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with cassette.recording(path, today, expect_exception=EXPECTED_ERRORS):
                module.Source(**args).fetch()
        except EXPECTED_ERRORS as exc:
            print(f"  recorded error case {slug(case_key)} ({type(exc).__name__})")
        except Exception as exc:
            _discard(path)
            print(
                f"  ! {case_key}: expected a SourceArgumentException, got "
                f"{type(exc).__name__}: {exc} -- not recorded"
            )
        else:
            # recording() treated the clean run as a success and wrote a
            # cassette with no expected_error; drop it, or the next replay
            # fails on a file this run said it had not written.
            _discard(path)
            print(
                f"  ! {case_key}: fetch() did not raise, not recorded -- is "
                "this case still expected to fail?"
            )


def record_cascading_choices(module_name: str) -> bool:
    """Record the HTTP for a cascading_select source's get_choices walk.

    Picks the TEST_CASE exercising the most cascade levels, then records
    ``get_choices(field, selections-so-far)`` for each populated level, storing
    the expected id per level so the offline test can assert each non-empty
    level's option list contains it. Returns True if it handled the source.
    """
    module = import_module(f"waste_collection_schedule.source.{module_name}")
    source_cls = module.Source
    params = getattr(source_cls, "PARAMS", [])
    casc = next((p for p in params if p.widget == "cascading_select"), None)
    if casc is None or not hasattr(source_cls, "get_choices"):
        return False
    fields = list(casc.fields)
    case = max(
        source_cls.TEST_CASES.values(),
        key=lambda c: sum(1 for f in fields if c.get(f) not in (None, "")),
    )
    context = {k: v for k, v in case.items() if k not in fields}
    expected = {f: case[f] for f in fields if case.get(f) not in (None, "")}
    if not expected:
        print(f"  ! {module_name}: no TEST_CASE populates a cascade level, skipped")
        return True

    today = datetime.date.today().isoformat()
    path = choices_path(module_name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    extra = {
        "widget": "cascading_select",
        "fields": fields,
        "context": context,
        "expected": expected,
    }
    try:
        with cassette.recording(path, today, extra=extra):
            selections = dict(context)
            for field in fields:
                if field not in expected:
                    continue
                source_cls.get_choices(field, dict(selections))
                selections[field] = expected[field]
        print(f"  recorded cascading choices for {module_name} ({list(expected)})")
    except Exception as exc:
        if os.path.exists(path):
            os.remove(path)
        print(f"  ! {module_name} choices: {type(exc).__name__}: {exc}")
    return True


def record_choices(module_name: str) -> None:
    """Record the HTTP for a dependent_select source's choice methods.

    For a source whose first PARAM is a ``dependent_select``, this captures the
    network for ``get_parent_choices()`` (when defined) and ``get_choices()``
    using the parent value from the first TEST_CASE, storing the expected parent
    and child values alongside so the offline test can assert against them.
    """
    if record_cascading_choices(module_name):
        return
    module = import_module(f"waste_collection_schedule.source.{module_name}")
    source_cls = module.Source
    params = getattr(source_cls, "PARAMS", [])
    dep = next((p for p in params if p.widget == "dependent_select"), None)
    if dep is None or not hasattr(source_cls, "get_choices"):
        return
    parent_field, child_field = list(dep.fields)[:2]
    case = next(iter(source_cls.TEST_CASES.values()))
    parent_value = case.get(parent_field)
    child_value = case.get(child_field)
    if not parent_value:
        print(f"  ! {module_name}: first TEST_CASE has no '{parent_field}', skipped")
        return

    today = datetime.date.today().isoformat()
    path = choices_path(module_name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    extra = {
        "parent_field": parent_field,
        "child_field": child_field,
        "parent_value": parent_value,
        "child_value": child_value,
    }
    try:
        with cassette.recording(path, today, extra=extra):
            if hasattr(source_cls, "get_parent_choices"):
                source_cls.get_parent_choices()
            source_cls.get_choices(parent_value)
        print(f"  recorded choices for {module_name} (parent={parent_value!r})")
    except Exception as exc:
        if os.path.exists(path):
            os.remove(path)
        print(f"  ! {module_name} choices: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    args = sys.argv[1:]
    modules = _new_arch_modules() if args == ["--all"] else args
    if not modules:
        print(__doc__)
        sys.exit(1)
    for mod in modules:
        print(f"== {mod} ==")
        record(mod)
        record_choices(mod)
        record_errors(mod)
