#!/usr/bin/env python3
"""One-shot helper: assign TITLE_LANG / DESCRIPTION_LANG / EXTRA_INFO_LANG
to sources whose COUNTRY suggests their TITLE / DESCRIPTION / EXTRA_INFO[]
.title strings are in a non-English language. Only assigns flags when:

* the source's COUNTRY (or filename suffix) maps to one of de / fr / it
* the existing lang flag is absent

This unblocks the per-language ``titles-de`` / ``titles-fr`` / ``titles-it``
matrix entries in ``.pyspelling.yml`` so titles like "Abfallwirtschaft Bad
Kreuznach" go through the German hunspell dictionary instead of failing
en_US.

Heuristic: country → language. False positives (sources where the title
is genuinely English even though the country is German-speaking) can be
fixed by adding an explicit ``TITLE_LANG = "en"`` to the source. Idempotent.
"""

from __future__ import annotations

import ast
import re
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

COUNTRY_LANG: dict[str, str] = {
    "de": "de",
    "at": "de",
    "ch": "de",  # German-speaking parts of CH; FR / IT cantons could override
    "fr": "fr",
    "lu": "fr",  # Luxembourg uses fr / de / lb; default fr
    "it": "it",
}


def _const_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _get_country(tree: ast.Module, filename: str) -> str | None:
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == "COUNTRY":
            return _const_str(node.value)
    # fall back to filename suffix (mimics get_source_by_file)
    suffix = filename.split("_")[-1]
    return suffix if suffix in COUNTRY_LANG or len(suffix) == 2 else None


def _has_top_level(tree: ast.Module, name: str) -> bool:
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == name:
                return True
    return False


def _has_member(tree: ast.Module, name: str) -> bool:
    """Whether the module defines ``name`` at the top level."""
    return _has_top_level(tree, name)


def _insert_lang_flags(text: str, flags: dict[str, str]) -> str:
    """Insert TITLE_LANG / DESCRIPTION_LANG / EXTRA_INFO_LANG assignments
    immediately after the corresponding TITLE / DESCRIPTION / EXTRA_INFO
    block. Each flag is appended only if the file doesn't already have it.
    """
    new_text = text
    for src, lang_name in (
        ("TITLE", "TITLE_LANG"),
        ("DESCRIPTION", "DESCRIPTION_LANG"),
        ("EXTRA_INFO", "EXTRA_INFO_LANG"),
    ):
        if lang_name in flags and not re.search(
            rf"^{lang_name}\s*=", new_text, flags=re.MULTILINE
        ):
            # find the line that ends the block: simplest reliable insertion
            # point is right after the first ``^TITLE = ...`` (or DESCRIPTION,
            # or EXTRA_INFO) statement. We use AST to locate it precisely.
            tree = ast.parse(new_text)
            insert_line = None
            for node in tree.body:
                if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                    continue
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id == src:
                    insert_line = (node.end_lineno or node.lineno)
                    break
            if insert_line is None:
                continue
            lines = new_text.splitlines(keepends=True)
            lines.insert(insert_line, f'{lang_name} = "{flags[lang_name]}"\n')
            new_text = "".join(lines)
    return new_text


def main() -> int:
    if not SOURCE_DIR.is_dir():
        print(f"missing {SOURCE_DIR}", file=sys.stderr)
        return 1

    rewritten = 0
    for py_path in sorted(SOURCE_DIR.glob("*.py")):
        if py_path.name == "__init__.py":
            continue
        text = py_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        country = _get_country(tree, py_path.stem)
        if not country:
            continue
        lang = COUNTRY_LANG.get(country.lower())
        if not lang:
            continue
        flags: dict[str, str] = {}
        if _has_top_level(tree, "TITLE") and not _has_top_level(tree, "TITLE_LANG"):
            flags["TITLE_LANG"] = lang
        if _has_top_level(tree, "DESCRIPTION") and not _has_top_level(tree, "DESCRIPTION_LANG"):
            flags["DESCRIPTION_LANG"] = lang
        if _has_top_level(tree, "EXTRA_INFO") and not _has_top_level(tree, "EXTRA_INFO_LANG"):
            flags["EXTRA_INFO_LANG"] = lang
        if not flags:
            continue
        new_text = _insert_lang_flags(text, flags)
        if new_text != text:
            py_path.write_text(new_text, encoding="utf-8", newline="\n")
            rewritten += 1
    print(f"rewrote {rewritten} sources with TITLE_LANG / DESCRIPTION_LANG / EXTRA_INFO_LANG")
    return 0


if __name__ == "__main__":
    sys.exit(main())
