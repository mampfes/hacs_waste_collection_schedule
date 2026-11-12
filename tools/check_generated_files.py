#!/usr/bin/env python3
"""Fail a PR that edits fully generated files.

These files are rewritten by the post-merge "Update generated documentation"
workflow (or, for the dashboard-card bundle, by ``npm run build``). Contributor
edits are overwritten or cause review noise, so this check blocks them.

Hybrid / partly generated files (README.md, info.md, translations/*.json) are
reported as warnings only: the country lists and ``config.step.args_*`` blocks
are generated, but the surrounding prose, ``options.step.init``, and
``translation_templates/`` are hand-maintained.

Usage::

    python tools/check_generated_files.py --base <sha-or-ref> [--head <sha>]

Exit 1 when a blocked path changed, 0 otherwise. Warnings go to stderr but do
not fail the check. The docs bot (``github-actions[bot]``, or ``GITHUB_ACTOR``)
is skipped entirely.
"""

from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = (
    REPO_ROOT
    / "custom_components"
    / "waste_collection_schedule"
    / "waste_collection_schedule"
    / "source"
)
DOC_SOURCE_DIR = REPO_ROOT / "doc" / "source"

# Generic / template pages under doc/source/ that are hand-maintained (or only
# have a patched service table) and must not be treated as fully generated.
HAND_MAINTAINED_SOURCE_DOCS = frozenset(
    {
        "ics.md",
        "static.md",
        "multiple.md",
        "example.md",
    }
)

SERVICE_SECTION_MARKER = "<!--Begin of service section-->"

BLOCKED_EXACT = frozenset(
    {
        "custom_components/waste_collection_schedule/sources.json",
        "custom_components/waste_collection_schedule/source_metadata.json",
        ".github/source_owners.json",
    }
)

# Rebuilt in PRs that change frontend/src; the frontend workflow already
# verifies the committed bundle matches a fresh build. Never hard-block these.
FRONTEND_GENERATED = frozenset(
    {
        "custom_components/waste_collection_schedule/frontend/waste-collection-cards.js",
        "custom_components/waste_collection_schedule/frontend/THIRD-PARTY-NOTICES.txt",
    }
)

WARN_EXACT = frozenset({"README.md", "info.md"})

DOCS_BOTS = frozenset({"github-actions[bot]"})


def _git_diff_names(base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACDMRTUXB", f"{base}...{head}"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _is_pipeline_source(stem: str) -> bool:
    """True when ``source/<stem>.py`` defines ``class Source(BaseSource)``."""
    path = SOURCE_DIR / f"{stem}.py"
    if not path.is_file():
        return False
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != "Source":
            continue
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "BaseSource":
                return True
            if isinstance(base, ast.Attribute) and base.attr == "BaseSource":
                return True
    return False


def _doc_has_service_section(path: Path) -> bool:
    try:
        return SERVICE_SECTION_MARKER in path.read_text(encoding="utf-8")
    except OSError:
        return False


def classify(path: str) -> str | None:
    """Return ``block``, ``warn``, or ``None`` (not a generated-file concern)."""
    posix = path.replace("\\", "/")
    if posix in FRONTEND_GENERATED:
        return None
    if posix in BLOCKED_EXACT:
        return "block"
    if posix in WARN_EXACT:
        return "warn"
    if posix.startswith(
        "custom_components/waste_collection_schedule/translations/"
    ) and posix.endswith(".json"):
        # args_* / reconfigure_* are generated; options.step.init and the rest
        # of the common UI are hand-maintained (or seeded from
        # translation_templates/). Do not hard-block.
        return "warn"
    if posix.startswith("doc/ics/") and posix.endswith(".md") and "/yaml/" not in posix:
        return "block"
    if posix.startswith("doc/source/") and posix.endswith(".md"):
        name = posix.rsplit("/", 1)[-1]
        if name in HAND_MAINTAINED_SOURCE_DOCS:
            return None
        stem = name[: -len(".md")]
        if not _is_pipeline_source(stem):
            # Legacy hand-written doc.
            return None
        if _doc_has_service_section(DOC_SOURCE_DIR / name):
            # Pipeline page with a patched, hand-written service section.
            return "warn"
        return "block"
    return None


def classify_paths(paths: list[str]) -> tuple[list[str], list[str]]:
    blocked: list[str] = []
    warnings: list[str] = []
    for path in paths:
        kind = classify(path)
        if kind == "block":
            blocked.append(path)
        elif kind == "warn":
            warnings.append(path)
    return blocked, warnings


def _is_docs_bot() -> bool:
    actor = os.environ.get("GITHUB_ACTOR", "")
    return actor in DOCS_BOTS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Base sha or ref (PR base)")
    parser.add_argument(
        "--head",
        default="HEAD",
        help="Head sha or ref (default: HEAD)",
    )
    args = parser.parse_args(argv)

    if _is_docs_bot():
        print(
            f"Skipping generated-file check for docs bot ({os.environ.get('GITHUB_ACTOR')})."
        )
        return 0

    changed = _git_diff_names(args.base, args.head)
    blocked, warnings = classify_paths(changed)

    if warnings:
        print(
            "Warning: this PR touches partly generated files. The generated "
            "portions (README/info country lists; translations config.step.args_* "
            "and reconfigure_*) are rewritten by the post-merge docs workflow. "
            "Leave those sections alone; hand-maintained parts (README/info "
            "prose, options.step.init, translation_templates/) are fine:\n  - "
            + "\n  - ".join(warnings),
            file=sys.stderr,
        )

    if blocked:
        print(
            "This PR edits fully generated files, which CI rewrites after merge "
            "(or, for pipeline source docs and doc/ics/*.md, update_docu_links.py "
            "on the next docs run). Please revert them with:\n\n"
            "  git checkout <base-branch> -- " + " ".join(blocked) + "\n\n"
            "Edit the source module, doc/ics/yaml/*.yaml, or the hand-maintained "
            "template instead. The dashboard-card bundle is exempt (rebuild it "
            "with `npm run build` in frontend/ when you change frontend/src). "
            "translations/*.json are not hard-blocked because options.step.init "
            "is hand-maintained.\n\nBlocked paths:\n  - " + "\n  - ".join(blocked),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
