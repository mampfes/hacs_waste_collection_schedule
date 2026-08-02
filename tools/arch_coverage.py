"""Report migration progress towards the BaseSource pipeline.

Run as an informational metric (it never fails the build)::

    python tools/arch_coverage.py

A source counts as *migrated* only when it is declarative: on the pipeline AND
composing shared components. A source that subclasses ``BaseSource`` but still
defines its own ``retrieve`` / ``parse`` / ``preprocess`` / ``transform`` has
put provider behaviour where the next provider on that platform cannot reach
it, so it is reported separately as debt rather than counted as done.

Pass ``--list`` to print the legacy modules still to migrate, and ``--debt`` to
print the pipeline sources still carrying their own steps.
"""

import ast
import sys
from pathlib import Path

SOURCE_DIR = (
    Path(__file__).resolve().parent.parent
    / "custom_components/waste_collection_schedule/waste_collection_schedule/source"
)
MARKER = "class Source(BaseSource)"
STEP_METHODS = ("retrieve", "parse", "preprocess", "transform")


def _overridden_steps(text: str) -> list[str]:
    """Step methods defined directly on a BaseSource subclass in this module."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    found: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(
            isinstance(base, ast.Name) and base.id == "BaseSource"
            for base in node.bases
        ):
            continue
        found += [
            member.name
            for member in node.body
            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
            and member.name in STEP_METHODS
        ]
    return found


def classify() -> tuple[list[str], list[tuple[str, list[str]]], list[str]]:
    """Return (declarative, [(module, overridden steps)], legacy) module names."""
    declarative: list[str] = []
    debt: list[tuple[str, list[str]]] = []
    legacy: list[str] = []
    for path in sorted(SOURCE_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        if MARKER not in text:
            legacy.append(path.stem)
            continue
        steps = _overridden_steps(text)
        if steps:
            debt.append((path.stem, sorted(set(steps))))
        else:
            declarative.append(path.stem)
    return declarative, debt, legacy


def main(argv: list[str]) -> int:
    declarative, debt, legacy = classify()
    pipeline = len(declarative) + len(debt)
    total = pipeline + len(legacy)
    done_pct = (100.0 * len(declarative) / total) if total else 0.0
    pipe_pct = (100.0 * pipeline / total) if total else 0.0

    print(
        f"Migrated (pipeline and fully declarative): "
        f"{len(declarative)}/{total} sources ({done_pct:.1f}%)"
    )
    print(f"On the pipeline at all:                    {pipeline}/{total} ({pipe_pct:.1f}%)")
    print(
        f"  still defining their own steps:          {len(debt)} "
        "(cleanup campaign, target zero)"
    )
    print(f"Legacy fetch() sources:                    {len(legacy)}")

    if "--debt" in argv:
        print("\nPipeline sources still defining their own steps:")
        for name, steps in debt:
            print(f"  {name}: {', '.join(steps)}")
    if "--list" in argv:
        print("\nLegacy (module-level fetch) sources still to migrate:")
        for name in legacy:
            print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
