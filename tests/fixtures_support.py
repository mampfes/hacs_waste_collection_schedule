"""Path/slug helpers for offline source cassettes.

A cassette is the recorded HTTP for one TEST_CASE, stored at
``tests/fixtures/<source_module>/<case_slug>.json`` (see ``cassette.py`` for the
record/replay machinery). Record or refresh with
``python tests/record_fixtures.py <module>``.
"""

from __future__ import annotations

import os
import re

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def slug(name: str) -> str:
    """Filesystem-safe slug for a TEST_CASE key."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def fixture_path(source_module: str, case_key: str, ext: str = "json") -> str:
    return os.path.join(FIXTURE_DIR, source_module, f"{slug(case_key)}.{ext}")


# Cassette holding the HTTP for a dependent_select source's choice methods
# (get_parent_choices / get_choices), kept separate from the fetch() cassettes.
CHOICES_FILENAME = "_choices.json"


def choices_path(source_module: str) -> str:
    return os.path.join(FIXTURE_DIR, source_module, CHOICES_FILENAME)


def discover_fixtures() -> list[tuple[str, str, str]]:
    """Return ``(source_module, case_slug, path)`` for every fetch fixture.

    Files starting with ``_`` (e.g. the dependent_select choices cassette) are
    not fetch cassettes and are skipped here.
    """
    found: list[tuple[str, str, str]] = []
    if not os.path.isdir(FIXTURE_DIR):
        return found
    for module in sorted(os.listdir(FIXTURE_DIR)):
        moddir = os.path.join(FIXTURE_DIR, module)
        if not os.path.isdir(moddir):
            continue
        for fname in sorted(os.listdir(moddir)):
            if fname.startswith("_"):
                continue
            case_slug = fname.rsplit(".", 1)[0]
            found.append((module, case_slug, os.path.join(moddir, fname)))
    return found


def discover_choice_fixtures() -> list[tuple[str, str]]:
    """Return ``(source_module, path)`` for every stored choices cassette."""
    found: list[tuple[str, str]] = []
    if not os.path.isdir(FIXTURE_DIR):
        return found
    for module in sorted(os.listdir(FIXTURE_DIR)):
        path = os.path.join(FIXTURE_DIR, module, CHOICES_FILENAME)
        if os.path.isfile(path):
            found.append((module, path))
    return found
