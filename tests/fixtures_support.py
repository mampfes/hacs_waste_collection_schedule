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


def discover_fixtures() -> list[tuple[str, str, str]]:
    """Return ``(source_module, case_slug, path)`` for every stored fixture."""
    found: list[tuple[str, str, str]] = []
    if not os.path.isdir(FIXTURE_DIR):
        return found
    for module in sorted(os.listdir(FIXTURE_DIR)):
        moddir = os.path.join(FIXTURE_DIR, module)
        if not os.path.isdir(moddir):
            continue
        for fname in sorted(os.listdir(moddir)):
            case_slug = fname.rsplit(".", 1)[0]
            found.append((module, case_slug, os.path.join(moddir, fname)))
    return found
