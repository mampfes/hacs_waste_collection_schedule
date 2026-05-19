"""Verify every source's ICON_MAP uses Icons.* enum references, not raw strings.

Walks the source directory, AST-parses each module, and checks that every
``ICON_MAP = {...}`` literal contains only ``Icons.<MEMBER>`` references on the
value side. Lists any source that still has raw ``"mdi:..."`` strings in
``ICON_MAP``.

This is the same check the pytest assertion enforces; running it manually is
useful when iterating on the migration scripts.

Run from the repo root::

    python script/icon_migration/04_verify.py
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_DIR = (
    REPO_ROOT
    / "custom_components"
    / "waste_collection_schedule"
    / "waste_collection_schedule"
    / "source"
)
EXCLUDE_FILENAMES = {"__init__.py", "example.py"}


def _find_icon_map_value(tree: ast.Module) -> ast.AST | None:
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if isinstance(target, ast.Name) and target.id == "ICON_MAP":
                return stmt.value
    return None


def _is_icons_attr(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "Icons"
    )


def main() -> int:
    bad: list[tuple[str, str, str]] = []  # (source, key, raw_value)
    dynamic: list[str] = []
    total_with_static_map = 0

    for path in sorted(SOURCE_DIR.glob("*.py")):
        if path.name in EXCLUDE_FILENAMES:
            continue
        source = path.stem
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            bad.append((source, "<file>", f"SyntaxError: {exc}"))
            continue

        node = _find_icon_map_value(tree)
        if node is None:
            continue

        if not isinstance(node, ast.Dict):
            dynamic.append(source)
            continue

        total_with_static_map += 1
        for key_node, val_node in zip(node.keys, node.values):
            key = key_node.value if isinstance(key_node, ast.Constant) else "<computed>"
            if _is_icons_attr(val_node):
                continue
            if isinstance(val_node, ast.Constant):
                bad.append((source, str(key), repr(val_node.value)))
            else:
                bad.append((source, str(key), ast.dump(val_node)))

    print(f"Sources with static ICON_MAP: {total_with_static_map}")
    print(f"Sources with non-static ICON_MAP (skipped): {len(dynamic)}")
    print(f"ICON_MAP values not using Icons enum: {len(bad)}")
    if bad:
        for source, key, value in bad[:50]:
            print(f"  {source} / {key!r} -> {value}")
        if len(bad) > 50:
            print(f"  ... and {len(bad) - 50} more")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
