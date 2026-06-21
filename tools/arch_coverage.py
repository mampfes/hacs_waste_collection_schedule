"""Report the share of source modules on the BaseSource pipeline.

Run as an informational metric (it never fails the build)::

    python tools/arch_coverage.py

Counts the source modules under ``source/`` and how many subclass
``BaseSource``, so migration progress (RFC #6561) is visible on every CI run.
Pass ``--list`` to also print the modules still on the legacy ``fetch()`` style.
"""

import sys
from pathlib import Path

SOURCE_DIR = (
    Path(__file__).resolve().parent.parent
    / "custom_components/waste_collection_schedule/waste_collection_schedule/source"
)
MARKER = "class Source(BaseSource)"


def classify() -> tuple[list[str], list[str]]:
    """Return (pipeline modules, legacy modules) by module name."""
    pipeline: list[str] = []
    legacy: list[str] = []
    for path in sorted(SOURCE_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        (pipeline if MARKER in text else legacy).append(path.stem)
    return pipeline, legacy


def main(argv: list[str]) -> int:
    pipeline, legacy = classify()
    total = len(pipeline) + len(legacy)
    pct = (100.0 * len(pipeline) / total) if total else 0.0
    print(f"BaseSource pipeline coverage: {len(pipeline)}/{total} sources ({pct:.1f}%)")
    if "--list" in argv:
        print("\nLegacy (module-level fetch) sources still to migrate:")
        for name in legacy:
            print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
