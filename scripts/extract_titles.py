#!/usr/bin/env python3
"""Extract TITLE / DESCRIPTION / EXTRA_INFO[].title strings from each source
module and group them by language for per-dictionary spell checking.

Source modules can declare a TITLE_LANG / DESCRIPTION_LANG / EXTRA_INFO_LANG
flag at module level (default ``"en"``) to indicate which hunspell dictionary
should check that string. For example a German-only provider:

    TITLE = "Abfallwirtschaft Bad Kreuznach"
    TITLE_LANG = "de"
    DESCRIPTION = "Mullabfuhrkalender fur Bad Kreuznach"
    DESCRIPTION_LANG = "de"

Output goes to ``build/i18n-extracted/titles_<lang>.txt`` with one phrase
per line. ``.pyspelling.yml`` references these files in its ``titles-<lang>``
matrix entries.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = (
    REPO_ROOT
    / "custom_components"
    / "waste_collection_schedule"
    / "waste_collection_schedule"
    / "source"
)
OUTPUT_DIR = REPO_ROOT / "build" / "i18n-extracted"
SUPPORTED_LANGS = ("en", "de", "fr", "it")


def _const(node: ast.AST | None) -> Any:
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _get_top_level(tree: ast.Module, name: str) -> Any:
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == name:
            value = _const(node.value)
            if value is not None:
                return value
    return None


def _get_extra_info_titles(tree: ast.Module) -> list[str]:
    """Best-effort extract of EXTRA_INFO[].title strings. Skips dynamic
    EXTRA_INFO definitions (function returning a list) — those are evaluated
    against runtime data we don't want to import here.
    """
    titles: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not (isinstance(target, ast.Name) and target.id == "EXTRA_INFO"):
            continue
        if not isinstance(node.value, ast.List):
            continue
        for elt in node.value.elts:
            if not isinstance(elt, ast.Dict):
                continue
            for k, v in zip(elt.keys, elt.values):
                if (
                    isinstance(k, ast.Constant)
                    and k.value == "title"
                    and isinstance(v, ast.Constant)
                    and isinstance(v.value, str)
                ):
                    titles.append(v.value)
    return titles


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    buckets: dict[str, list[str]] = {lang: [] for lang in SUPPORTED_LANGS}

    for py_path in sorted(SOURCE_DIR.glob("*.py")):
        if py_path.name == "__init__.py":
            continue
        try:
            tree = ast.parse(py_path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        title = _get_top_level(tree, "TITLE")
        description = _get_top_level(tree, "DESCRIPTION")
        title_lang = _get_top_level(tree, "TITLE_LANG") or "en"
        description_lang = _get_top_level(tree, "DESCRIPTION_LANG") or "en"
        extra_info_lang = _get_top_level(tree, "EXTRA_INFO_LANG") or "en"
        extra_info_titles = _get_extra_info_titles(tree)

        if isinstance(title, str) and title_lang in buckets:
            buckets[title_lang].append(f"# {py_path.stem} TITLE")
            buckets[title_lang].append(title)
        if isinstance(description, str) and description_lang in buckets:
            buckets[description_lang].append(f"# {py_path.stem} DESCRIPTION")
            buckets[description_lang].append(description)
        if extra_info_titles and extra_info_lang in buckets:
            for t in extra_info_titles:
                buckets[extra_info_lang].append(f"# {py_path.stem} EXTRA_INFO")
                buckets[extra_info_lang].append(t)

    for lang, lines in buckets.items():
        out = OUTPUT_DIR / f"titles_{lang}.txt"
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{out.relative_to(REPO_ROOT)}: {len(lines)} lines")

    return 0


if __name__ == "__main__":
    sys.exit(main())
