#!/usr/bin/env python3
"""Concatenate base + per-source wordlists into per-language build files.

Mirrors the i18n catalog structure: project-wide allowed words live in
``.spelling/<lang>.wordlist``; source-specific names / acronyms live next
to the source module at
``custom_components/.../source/<source_id>.i18n/<lang>.wordlist``. This
script merges both layers into ``build/spelling/<lang>.wordlist``, which
``.pyspelling.yml`` consumes.

Run before ``pyspelling -c .pyspelling.yml``. CI does this automatically;
locally::

    python scripts/build_wordlists.py
    pyspelling -c .pyspelling.yml
"""
from __future__ import annotations

import argparse
from pathlib import Path

LANGUAGES = ("en", "de", "fr", "it")
REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_MODULE_DIR = (
    REPO_ROOT
    / "custom_components"
    / "waste_collection_schedule"
    / "waste_collection_schedule"
    / "source"
)


def _word_lines(text: str) -> list[str]:
    """Strip blanks and comments, keep order, dedupe."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in text.splitlines():
        word = raw.strip()
        if not word or word.startswith("#"):
            continue
        if word in seen:
            continue
        seen.add(word)
        out.append(word)
    return out


def _per_source_wordlists(lang: str) -> list[Path]:
    """Yield every ``source/<id>.i18n/<lang>.wordlist`` present on disk."""
    if not SOURCE_MODULE_DIR.is_dir():
        return []
    return sorted(SOURCE_MODULE_DIR.glob(f"*.i18n/{lang}.wordlist"))


def build(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    spelling_dir = REPO_ROOT / ".spelling"

    for lang in LANGUAGES:
        merged: list[str] = []
        seen: set[str] = set()

        def add(path: Path) -> int:
            count = 0
            for word in _word_lines(path.read_text(encoding="utf-8")):
                if word not in seen:
                    seen.add(word)
                    merged.append(word)
                    count += 1
            return count

        base = spelling_dir / f"{lang}.wordlist"
        base_count = add(base) if base.exists() else 0

        per_source_files = _per_source_wordlists(lang)
        per_source_count = sum(add(p) for p in per_source_files)

        out_path = out_dir / f"{lang}.wordlist"
        out_path.write_text("\n".join(merged) + "\n", encoding="utf-8")
        print(
            f"[{lang}] {out_path.relative_to(REPO_ROOT)}: "
            f"{base_count} base + {per_source_count} from "
            f"{len(per_source_files)} per-source file(s) = "
            f"{len(merged)} unique words"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default="build/spelling",
        help="Output directory (default: build/spelling)",
    )
    args = parser.parse_args()
    build(REPO_ROOT / args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
