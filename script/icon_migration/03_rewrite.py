"""Rewrite each source's ICON_MAP from raw mdi:* strings to Icons.* enum refs.

For every classified source:
  1. AST-parse the source file to find the line range of the ``ICON_MAP = {...}``
     assignment.
  2. Generate a new dict literal using ``Icons.<CATEGORY>`` values.
  3. Replace that line range in the file text.
  4. Update the ``from waste_collection_schedule import ...`` line to include
     ``Icons`` if it isn't already there.

Notes
-----
* Comments *inside* the ICON_MAP dict are lost (rare in practice).
* All other comments and formatting are preserved (line-range replacement only
  touches the dict literal itself and the import line).
* Idempotent: re-running after a classification correction produces the same
  output.

Run from the repo root::

    python script/icon_migration/03_rewrite.py
"""

from __future__ import annotations

import ast
import json
import re
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
CLASSIFIED_DIR = Path(__file__).resolve().parent / "classified"


def _find_icon_map_span(tree: ast.Module) -> tuple[int, int, ast.Dict] | None:
    """Return (start_line, end_line, dict_node) for the ICON_MAP assignment.

    Handles both ``ICON_MAP = {...}`` and ``ICON_MAP: dict = {...}`` forms.
    Lines are 1-based and inclusive. Returns None if no static ICON_MAP found.
    """
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "ICON_MAP":
                    if isinstance(stmt.value, ast.Dict):
                        return stmt.lineno, stmt.end_lineno or stmt.lineno, stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            if isinstance(stmt.target, ast.Name) and stmt.target.id == "ICON_MAP":
                if isinstance(stmt.value, ast.Dict):
                    return stmt.lineno, stmt.end_lineno or stmt.lineno, stmt.value
    return None


def _render_icon_map(
    keys: list[str], categories: dict[str, str], indent: str = "    "
) -> str:
    """Render the new ICON_MAP literal in canonical formatting."""
    lines = ["ICON_MAP = {"]
    for key in keys:
        cat = categories[key]
        # Use double quotes for the key, escape any internal " characters.
        key_repr = '"' + key.replace("\\", "\\\\").replace('"', '\\"') + '"'
        lines.append(f"{indent}{key_repr}: Icons.{cat},")
    lines.append("}")
    return "\n".join(lines)


_IMPORT_RE_BARE = re.compile(
    r"^(from\s+waste_collection_schedule\s+import\s+)([^\n#]+?)(\s*(#.*)?)$"
)
_REL_COLLECTION_RE = re.compile(r"^from\s+\.\.collection\s+import\s+Collection")
_ABS_COLLECTION_RE = re.compile(r"^from\s+waste_collection_schedule\.collection\s+import\s+")


def _update_import_line(text: str) -> tuple[str, bool]:
    """Ensure ``Icons`` is imported.

    Strategies, in order:
      1. Modify an existing single-line ``from waste_collection_schedule import ...``
         to add ``Icons`` to its names.
      2. If a relative ``from ..collection import Collection`` exists, insert a
         new ``from ..icons import Icons`` after it.
      3. If an absolute ``from waste_collection_schedule.collection import ...``
         exists (single- or multi-line), insert ``from waste_collection_schedule.icons import Icons``
         immediately after the import block (the first non-import/non-blank line
         in the file after the import).
      4. Otherwise, insert ``from waste_collection_schedule import Icons  # type: ignore[attr-defined]``
         after the last top-of-file import line.

    Idempotent — if ``Icons`` is already imported anywhere, returns unchanged.
    """
    # Idempotency check: look for `Icons` in import lines only (the dict-value
    # rewrite already inserts `Icons.X` references which would false-positive
    # a naive `\bIcons\b` search).
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("from ") or stripped.startswith("import ")):
            continue
        if re.search(r"\bIcons\b", stripped):
            return text, True

    lines = text.splitlines(keepends=True)

    # Strategy 1: single-line `from waste_collection_schedule import ...`
    for i, line in enumerate(lines):
        m = _IMPORT_RE_BARE.match(line.rstrip("\n"))
        if not m:
            continue
        prefix, names, trailing, _comment = m.groups()
        parsed = [n.strip() for n in re.split(r",\s*", names.strip("() ")) if n.strip()]
        if "Icons" in parsed:
            return text, True
        parsed.append("Icons")
        new_names = ", ".join(sorted(parsed))
        nl = "\n" if line.endswith("\n") else ""
        lines[i] = f"{prefix}{new_names}{trailing}{nl}"
        return "".join(lines), True

    # Strategy 2: relative `from ..collection import Collection`
    for i, line in enumerate(lines):
        if _REL_COLLECTION_RE.match(line.rstrip("\n")):
            indent = re.match(r"^(\s*)", line).group(1) or ""
            insert = f"{indent}from ..icons import Icons\n"
            lines.insert(i + 1, insert)
            return "".join(lines), True

    # Strategy 3: absolute submodule import
    for i, line in enumerate(lines):
        if _ABS_COLLECTION_RE.match(line.rstrip("\n")):
            # Find end of this import (it might be multi-line with parens).
            end = i
            paren_open = "(" in line and ")" not in line
            while paren_open and end + 1 < len(lines):
                end += 1
                if ")" in lines[end]:
                    paren_open = False
            insert = "from waste_collection_schedule.icons import Icons\n"
            lines.insert(end + 1, insert)
            return "".join(lines), True

    # Strategy 4: AST-based — find the end line of the last top-level import.
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text, False
    last_end_line = 0
    for stmt in tree.body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            last_end_line = max(last_end_line, stmt.end_lineno or stmt.lineno)
    if last_end_line > 0:
        insert = "from waste_collection_schedule import Icons  # type: ignore[attr-defined]\n"
        # Insert after line index (last_end_line - 1) → at position last_end_line.
        lines.insert(last_end_line, insert)
        return "".join(lines), True

    return text, False


def rewrite_source(source_name: str, classified: dict) -> tuple[bool, str]:
    """Rewrite a single source. Returns (changed, reason)."""
    path = SOURCE_DIR / f"{source_name}.py"
    if not path.exists():
        return False, f"source file not found: {path}"

    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return False, f"syntax error: {exc}"

    span = _find_icon_map_span(tree)
    if span is None:
        return False, "no static ICON_MAP found"

    start_line, end_line, dict_node = span

    # Extract the keys in their original AST order.
    keys: list[str] = []
    for k in dict_node.keys:
        if not isinstance(k, ast.Constant) or not isinstance(k.value, str):
            return False, "ICON_MAP has non-string key"
        keys.append(k.value)

    categories = classified["mapping"]
    missing = [k for k in keys if k not in categories]
    if missing:
        return False, f"classified mapping missing keys: {missing}"

    new_block = _render_icon_map(keys, categories)

    # Replace lines [start_line .. end_line] (1-based, inclusive) with new_block.
    lines = text.splitlines(keepends=True)
    # Preserve trailing newline on the last replaced line.
    before = "".join(lines[: start_line - 1])
    after = "".join(lines[end_line:])
    # Add a newline after new_block to keep the file structure clean (matches
    # the original ICON_MAP block which ended with `\n` after `}`).
    if not new_block.endswith("\n"):
        new_block = new_block + "\n"
    new_text = before + new_block + after

    # Update import line.
    new_text, import_changed = _update_import_line(new_text)
    if not import_changed:
        return False, "ICON_MAP rewritten but couldn't update import line"

    if new_text == text:
        return False, "no change"

    path.write_text(new_text, encoding="utf-8")
    return True, "rewritten"


def main() -> int:
    rewritten = 0
    skipped = 0
    failed: list[tuple[str, str]] = []

    for json_path in sorted(CLASSIFIED_DIR.glob("*.json")):
        source_name = json_path.stem
        classified = json.loads(json_path.read_text(encoding="utf-8"))
        ok, reason = rewrite_source(source_name, classified)
        if ok:
            rewritten += 1
        else:
            if reason in ("no change",):
                skipped += 1
            else:
                failed.append((source_name, reason))

    print(f"Rewrote {rewritten} source files.")
    print(f"Skipped (no change needed): {skipped}.")
    print(f"Failed: {len(failed)}.")
    for source, reason in failed:
        print(f"  - {source}: {reason}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
