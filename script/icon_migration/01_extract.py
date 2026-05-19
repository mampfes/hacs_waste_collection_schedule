"""AST-walk every source module and extract its module-level ICON_MAP literal.

Emits one JSON per source under script/icon_migration/extracted/<source>.json:

    {
        "source": "amberg_de",
        "title": "Amberg",
        "country": "de",
        "icon_map": {"Rest- und Biomüll": "mdi:trash-can", ...},
        "is_dict_literal": True
    }

Sources whose ICON_MAP is not a static dict literal (e.g. constructed with a
dict comprehension, conditional assignment, or imported) are listed in
script/icon_migration/skipped.txt for manual handling.

Run from the repo root::

    python script/icon_migration/01_extract.py
"""

from __future__ import annotations

import ast
import json
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
OUT_DIR = Path(__file__).resolve().parent / "extracted"
SKIPPED_FILE = Path(__file__).resolve().parent / "skipped.txt"

EXCLUDE_FILENAMES = {"__init__.py", "example.py"}


def _string_value(node: ast.AST) -> str | None:
    """Return the string literal value of a node, or None if it isn't one."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _extract_module_constants(tree: ast.Module) -> dict[str, ast.AST]:
    """Map top-level assignment target names to their value AST nodes.

    Handles both ``X = ...`` and ``X: T = ...`` forms.
    """
    out: dict[str, ast.AST] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    out[target.id] = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            if isinstance(stmt.target, ast.Name):
                out[stmt.target.id] = stmt.value
    return out


def _icon_map_from_dict_node(node: ast.AST) -> dict[str, str] | None:
    """Try to read a `{key: value}` literal where keys are strings and values
    are either string literals (raw mdi:* strings) or already-Icons references.
    Returns None when the node isn't a static dict we can read.
    """
    if not isinstance(node, ast.Dict):
        return None
    out: dict[str, str] = {}
    for key, value in zip(node.keys, node.values):
        key_str = _string_value(key) if key is not None else None
        if key_str is None:
            # f-strings, computed keys, or `**spread` — give up; this dict
            # isn't fully static.
            return None
        value_str: str | None = _string_value(value)
        if value_str is None and isinstance(value, ast.Attribute):
            # Already an `Icons.SOMETHING` reference — capture as marker.
            if isinstance(value.value, ast.Name) and value.value.id == "Icons":
                value_str = f"Icons.{value.attr}"
        if value_str is None:
            # Computed value we can't statically resolve.
            return None
        out[key_str] = value_str
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    skipped: list[tuple[str, str]] = []  # (source, reason)
    extracted_count = 0

    for path in sorted(SOURCE_DIR.glob("*.py")):
        if path.name in EXCLUDE_FILENAMES:
            continue

        source_name = path.stem
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            skipped.append((source_name, f"SyntaxError: {exc}"))
            continue

        constants = _extract_module_constants(tree)

        if "ICON_MAP" not in constants:
            # Many sources have no ICON_MAP at all — that's fine; nothing to migrate.
            continue

        icon_map = _icon_map_from_dict_node(constants["ICON_MAP"])
        if icon_map is None:
            skipped.append(
                (source_name, "ICON_MAP is not a static dict literal we can read")
            )
            continue

        title_node = constants.get("TITLE")
        country_node = constants.get("COUNTRY")
        title = _string_value(title_node) if title_node is not None else None
        country = _string_value(country_node) if country_node is not None else None

        payload = {
            "source": source_name,
            "title": title,
            "country": country,
            "icon_map": icon_map,
            "is_dict_literal": True,
        }
        (OUT_DIR / f"{source_name}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        extracted_count += 1

    SKIPPED_FILE.write_text(
        "\n".join(f"{s}\t{r}" for s, r in skipped) + ("\n" if skipped else ""),
        encoding="utf-8",
    )

    total = sum(1 for p in SOURCE_DIR.glob("*.py") if p.name not in EXCLUDE_FILENAMES)
    print(f"Scanned {total} source files.")
    print(f"Extracted ICON_MAP for {extracted_count} sources to {OUT_DIR}.")
    print(f"Skipped {len(skipped)} (see {SKIPPED_FILE}).")
    print(f"Sources without ICON_MAP: {total - extracted_count - len(skipped)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
