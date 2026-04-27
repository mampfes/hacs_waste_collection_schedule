#!/usr/bin/env python3
"""AST-aware rename helper for the 'manual review' cases that
``normalize_param_names.py`` had to skip because the OLD name appears as a
dict-key string literal (an external API key).

Renames every reference to the old name as a Python identifier, plus the
matching YAML override key, but PRESERVES string literals used as dict
keys outside the TEST_CASES block (those are the API contracts).

Usage:
    python scripts/force_rename_param.py <source_id> <old1>=<new1> [<old2>=<new2> ...]

Examples:
    python scripts/force_rename_param.py aha_region_de gemeinde=municipality strasse=street
    python scripts/force_rename_param.py wellington_govt_nz streetId=street_id streetName=street_name
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
I18N_SOURCES_DIR = (
    REPO_ROOT / "custom_components" / "waste_collection_schedule" / "i18n" / "sources"
)


def collect_protected_positions(tree: ast.Module, names: set[str]) -> set[tuple[int, int]]:
    """Find (lineno, col_offset) of dict-key string literals OUTSIDE TEST_CASES
    whose value matches one of ``names``. Those positions must NOT be renamed.
    """
    test_cases_range = None
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "TEST_CASES"
        ):
            test_cases_range = (node.lineno, node.end_lineno or node.lineno)
            break

    protected: set[tuple[int, int]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key in node.keys:
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                continue
            if key.value not in names:
                continue
            lineno = key.lineno or 0
            if test_cases_range and test_cases_range[0] <= lineno <= test_cases_range[1]:
                continue
            protected.add((key.lineno, key.col_offset))
    return protected


def rewrite_text(text: str, renames: dict[str, str], protected: set[tuple[int, int]]) -> str:
    """Word-boundary rename old->new in ``text`` while leaving ``protected``
    positions unchanged. ``protected`` carries (lineno, col_offset) of string
    literals that must keep their old value.

    The string-literal column offset points at the opening quote, so the
    actual identifier text starts at col_offset + 1. We treat any match
    starting within the quoted region as protected.
    """
    # Build a lookup: for each line, the list of column ranges that are
    # forbidden. The string literal's content starts one char after the
    # quote and is `len(old)` long.
    forbidden: dict[int, list[tuple[int, int]]] = {}
    for lineno, col in protected:
        # We don't know which old name was at that position, but the ranges
        # for all rename targets at that line are checked below.
        forbidden.setdefault(lineno, []).append((col, col + max(len(o) for o in renames) + 2))

    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines, 1):
        if not any(old in line for old in renames):
            continue
        line_forbidden = forbidden.get(i, [])

        def is_in_forbidden(start: int, end: int) -> bool:
            for f_lo, f_hi in line_forbidden:
                # f_lo points at opening quote; literal content [f_lo+1 ... ]
                if f_lo <= start <= f_hi:
                    return True
            return False

        new_line = []
        idx = 0
        while idx < len(line):
            replaced = False
            for old, new in renames.items():
                pat = re.compile(rf"\b{re.escape(old)}\b")
                m = pat.match(line, idx)
                if m and not is_in_forbidden(m.start(), m.end()):
                    new_line.append(new)
                    idx = m.end()
                    replaced = True
                    break
            if not replaced:
                new_line.append(line[idx])
                idx += 1
        lines[i - 1] = "".join(new_line)
    return "".join(lines)


def rewrite_yaml_keys(yaml_path: Path, renames: dict[str, str]) -> bool:
    text = yaml_path.read_text(encoding="utf-8")
    new_text = text
    for old, new in renames.items():
        new_text = re.sub(
            rf"^(\s+){re.escape(old)}:",
            rf"\1{new}:",
            new_text,
            flags=re.MULTILINE,
        )
    if new_text == text:
        return False
    yaml_path.write_text(new_text, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 1

    source_id = sys.argv[1]
    renames: dict[str, str] = {}
    for arg in sys.argv[2:]:
        if "=" not in arg:
            print(f"bad arg {arg!r}, expected old=new", file=sys.stderr)
            return 1
        old, new = arg.split("=", 1)
        renames[old] = new

    py_path = SOURCE_DIR / f"{source_id}.py"
    if not py_path.is_file():
        print(f"source not found: {py_path}", file=sys.stderr)
        return 1

    text = py_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    protected = collect_protected_positions(tree, set(renames.keys()))

    new_text = rewrite_text(text, renames, protected)
    if new_text != text:
        py_path.write_text(new_text, encoding="utf-8", newline="\n")
        print(f"rewrote {py_path.relative_to(REPO_ROOT)}")

    yaml_dir = I18N_SOURCES_DIR / source_id
    if yaml_dir.is_dir():
        for yaml_path in sorted(yaml_dir.glob("*.yaml")):
            if rewrite_yaml_keys(yaml_path, renames):
                print(f"rewrote {yaml_path.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
