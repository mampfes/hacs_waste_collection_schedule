"""Dump every collection a cassette replays to, for before/after refactor diffs.

Offline replay only asserts a source yields valid collections, so on its own it
cannot tell a refactor from a behaviour change. This prints the actual output,
so the two runs can be diffed:

    python tests/dump_collections.py okc_gov > before.txt
    ... refactor ...
    python tests/dump_collections.py okc_gov > after.txt
    diff before.txt after.txt

With no module names it dumps every cassette in the tree.
"""

import calendar  # noqa: F401 - import stdlib calendar before the package path
import contextlib
import os
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
from fixtures_support import discover_fixtures, slug


def _resolve_case(module_name: str, case_slug: str):
    module = import_module(f"waste_collection_schedule.source.{module_name}")
    for key, args in module.Source.TEST_CASES.items():
        if slug(key) == case_slug:
            return module.Source, args
    return None, None


def main(wanted: "list[str]") -> int:
    for module_name, case_slug, path in sorted(discover_fixtures()):
        if wanted and module_name not in wanted:
            continue
        cls, args = _resolve_case(module_name, case_slug)
        if cls is None:
            print(f"{module_name}::{case_slug}: NO MATCHING TEST_CASE")
            continue
        try:
            # A source may print its own warnings ("unresolved waste type ...")
            # while fetching. Those land mid-line in this dump and move about
            # between runs, which reads as a diff when nothing changed.
            with (
                open(os.devnull, "w") as quiet,
                contextlib.redirect_stdout(quiet),
                contextlib.redirect_stderr(quiet),
                cassette.replaying(path),
            ):
                results = cls(**args).fetch()
        except Exception as error:
            print(f"{module_name}::{case_slug}: RAISED {type(error).__name__}: {error}")
            continue
        rows = sorted(f"{r.date.isoformat()} {r.waste_type}" for r in results)
        print(f"{module_name}::{case_slug}: {len(rows)} collections")
        for row in rows:
            print(f"  {row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
