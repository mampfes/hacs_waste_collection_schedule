#!/usr/bin/env python3
"""One-shot migration: lift PARAM_TRANSLATIONS / PARAM_DESCRIPTIONS out of
source .py files into per-source YAML override files under
``custom_components/waste_collection_schedule/i18n/sources/<source_id>/``.

What this script does, per source file:

1. Parses the .py with ``ast`` and locates the top-level ``PARAM_TRANSLATIONS``
   and ``PARAM_DESCRIPTIONS`` assignments. ``ast.literal_eval`` resolves the
   dict literal so we keep nested string values intact.
2. For every ``(lang, param, value)`` triple, checks whether the shared
   registry under ``i18n/shared/<lang>.yaml`` already has the same value for
   that ``param``. Matching entries are dropped (the DRY win — they
   re-resolve through the shared registry at generator time).
3. The residue (overrides + novel keys) is written to
   ``i18n/sources/<source_id>/<lang>.yaml``. No file is created when a
   language has no residue for a source.
4. The ``PARAM_TRANSLATIONS`` and ``PARAM_DESCRIPTIONS`` assignments are
   removed from the .py file, taking any immediately-preceding comment lines
   that describe them along for the ride. Trailing blank lines around the
   removed block are collapsed.

The script is idempotent on a clean checkout: a second run finds nothing to
migrate. It does not touch files that have neither dict.

After running, ``update_docu_links.py`` must be re-pointed at the i18n
catalogs so its output stays byte-identical.

Usage:
    python scripts/migrate_i18n.py [--dry-run] [--source <source_id>] [...]
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = (
    REPO_ROOT
    / "custom_components"
    / "waste_collection_schedule"
    / "waste_collection_schedule"
    / "source"
)
I18N_ROOT = REPO_ROOT / "custom_components" / "waste_collection_schedule" / "i18n"
SHARED_DIR = I18N_ROOT / "shared"
SOURCES_DIR = I18N_ROOT / "sources"
LANGUAGES = ("en", "de", "fr", "it")
TARGET_NAMES = ("PARAM_TRANSLATIONS", "PARAM_DESCRIPTIONS")


def load_shared() -> dict[str, dict[str, dict[str, str]]]:
    """Return shared[lang][param] -> {label, description}."""
    shared: dict[str, dict[str, dict[str, str]]] = {}
    for lang in LANGUAGES:
        path = SHARED_DIR / f"{lang}.yaml"
        if not path.is_file():
            shared[lang] = {}
            continue
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        shared[lang] = data.get("params") or {}
    return shared


def find_assignments(tree: ast.Module) -> dict[str, ast.Assign]:
    """Return {name: Assign node} for top-level matches in TARGET_NAMES."""
    found: dict[str, ast.Assign] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id in TARGET_NAMES:
            found[target.id] = node
    return found


def collect_module_constants(tree: ast.Module) -> dict[str, Any]:
    """Collect top-level ``NAME = <literal>`` assignments so we can resolve
    Name references inside the target dicts (e.g. ``GROUP_DESCRIPTION_EN``).
    """
    consts: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            consts[target.id] = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue  # not a literal — ignore
    return consts


def _eval_node(node: ast.AST, env: dict[str, Any]) -> Any:
    """Tiny static evaluator: literals plus Name lookup against ``env``.

    Raises ValueError for anything we can't handle, so callers can flag the
    source for manual review.
    """
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in env:
            raise ValueError(f"unresolved name {node.id!r}")
        return env[node.id]
    if isinstance(node, ast.Dict):
        return {
            _eval_node(k, env): _eval_node(v, env)
            for k, v in zip(node.keys, node.values)
            if k is not None  # skip dict unpacking
        }
    if isinstance(node, ast.List):
        return [_eval_node(elt, env) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(elt, env) for elt in node.elts)
    raise ValueError(f"unsupported node type {type(node).__name__}")


def extract_dict(
    node: ast.Assign, consts: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """Resolve the assigned value as a Python literal, or None if it's not a
    plain dict we can statically migrate. ``consts`` lets us resolve simple
    Name references to other module-level string constants.
    """
    try:
        value = _eval_node(node.value, consts or {})
    except (ValueError, SyntaxError):
        return None
    if not isinstance(value, dict):
        return None
    return value


def diff_against_shared(
    raw: dict[str, Any],
    shared: dict[str, dict[str, dict[str, str]]],
    field: str,
) -> dict[str, dict[str, str]]:
    """Return the residue per-language after dropping shared duplicates.

    ``raw`` is the source's ``PARAM_TRANSLATIONS`` (field='label') or
    ``PARAM_DESCRIPTIONS`` (field='description') dict shaped as
    ``{lang: {param: value}}``. The output keeps only entries whose value
    differs from the shared registry's ``field`` for the same param.
    """
    residue: dict[str, dict[str, str]] = {}
    for lang, params in raw.items():
        if not isinstance(params, dict):
            continue
        per_lang: dict[str, str] = {}
        shared_lang = shared.get(lang, {})
        for param, value in params.items():
            if not isinstance(value, str):
                continue
            shared_entry = shared_lang.get(param)
            if isinstance(shared_entry, dict) and shared_entry.get(field) == value:
                continue  # already covered by shared registry
            per_lang[param] = value
        if per_lang:
            residue[lang] = per_lang
    return residue


def merge_residue(
    translations_residue: dict[str, dict[str, str]],
    descriptions_residue: dict[str, dict[str, str]],
) -> dict[str, dict[str, dict[str, str]]]:
    """Combine label and description residues into per-language YAML shape:
    ``{lang: {param: {label?, description?}}}``.
    """
    merged: dict[str, dict[str, dict[str, str]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    for lang, params in translations_residue.items():
        for param, value in params.items():
            merged[lang][param]["label"] = value
    for lang, params in descriptions_residue.items():
        for param, value in params.items():
            merged[lang][param]["description"] = value
    return {lang: dict(params) for lang, params in merged.items()}


def write_yaml_dump(data: dict[str, Any]) -> str:
    """Dump dict as YAML with consistent block style."""
    return yaml.safe_dump(
        data,
        sort_keys=True,
        allow_unicode=True,
        default_flow_style=False,
        width=80,
    )


def write_source_overrides(
    source_id: str,
    merged: dict[str, dict[str, dict[str, str]]],
    *,
    dry_run: bool,
) -> list[Path]:
    """Write per-language override files. Returns paths written."""
    written: list[Path] = []
    if not merged:
        return written
    target_dir = SOURCES_DIR / source_id
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
    for lang, params in merged.items():
        if not params:
            continue
        path = target_dir / f"{lang}.yaml"
        body = write_yaml_dump({"params": params})
        content = (
            f"# Per-source overrides for {source_id} ({lang}).\n"
            "# Generated by scripts/migrate_i18n.py from the original PARAM_TRANSLATIONS\n"
            "# and PARAM_DESCRIPTIONS dicts. Edit freely.\n"
            "---\n"
            f"{body}"
        )
        if dry_run:
            print(f"  WOULD WRITE {path.relative_to(REPO_ROOT)} ({len(params)} params)")
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
            written.append(path)
    return written


def remove_assignments(
    text: str,
    assignments: dict[str, ast.Assign],
) -> str:
    """Return ``text`` with the given top-level assignments removed.

    Drops the assignment's full line range plus any single immediately-
    preceding comment line (which typically narrates the dict's purpose), and
    collapses neighbouring blank lines to at most one.
    """
    if not assignments:
        return text

    lines = text.splitlines(keepends=True)
    drop = [False] * len(lines)
    for node in assignments.values():
        start = node.lineno - 1
        end = (node.end_lineno or node.lineno) - 1
        # absorb a single preceding comment line that documents this dict
        if start - 1 >= 0 and lines[start - 1].lstrip().startswith("#"):
            start -= 1
        for i in range(start, end + 1):
            drop[i] = True

    out: list[str] = []
    prev_blank = False
    for keep_line, line in zip((not d for d in drop), lines):
        if not keep_line:
            prev_blank = False
            continue
        is_blank = line.strip() == ""
        if is_blank and prev_blank:
            continue
        out.append(line)
        prev_blank = is_blank
    return "".join(out)


def migrate_one(
    py_path: Path,
    shared: dict[str, dict[str, dict[str, str]]],
    *,
    dry_run: bool,
) -> dict[str, Any]:
    """Migrate a single source file. Returns a stats dict."""
    text = py_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(py_path))
    except SyntaxError as exc:
        return {"source_id": py_path.stem, "error": f"parse: {exc}"}

    assignments = find_assignments(tree)
    if not assignments:
        return {"source_id": py_path.stem, "skipped": True}

    consts = collect_module_constants(tree)
    raw_translations = {}
    raw_descriptions = {}
    static_assignments: dict[str, ast.Assign] = {}
    dynamic_names: list[str] = []

    if "PARAM_TRANSLATIONS" in assignments:
        result = extract_dict(assignments["PARAM_TRANSLATIONS"], consts)
        if result is None:
            dynamic_names.append("PARAM_TRANSLATIONS")
        else:
            raw_translations = result
            static_assignments["PARAM_TRANSLATIONS"] = assignments["PARAM_TRANSLATIONS"]

    if "PARAM_DESCRIPTIONS" in assignments:
        result = extract_dict(assignments["PARAM_DESCRIPTIONS"], consts)
        if result is None:
            dynamic_names.append("PARAM_DESCRIPTIONS")
        else:
            raw_descriptions = result
            static_assignments["PARAM_DESCRIPTIONS"] = assignments["PARAM_DESCRIPTIONS"]

    translations_residue = diff_against_shared(raw_translations, shared, field="label")
    descriptions_residue = diff_against_shared(
        raw_descriptions, shared, field="description"
    )
    merged = merge_residue(translations_residue, descriptions_residue)

    written = write_source_overrides(py_path.stem, merged, dry_run=dry_run)

    new_text = remove_assignments(text, static_assignments)
    if not dry_run and new_text != text:
        py_path.write_text(new_text, encoding="utf-8", newline="\n")

    return {
        "source_id": py_path.stem,
        "translations_total": sum(len(v) for v in raw_translations.values()),
        "descriptions_total": sum(len(v) for v in raw_descriptions.values()),
        "translations_kept": sum(len(v) for v in translations_residue.values()),
        "descriptions_kept": sum(len(v) for v in descriptions_residue.values()),
        "languages_with_residue": sorted(merged.keys()),
        "wrote": [str(p.relative_to(REPO_ROOT)) for p in written],
        "stripped": list(static_assignments.keys()),
        "manual_review": dynamic_names,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print what would change without writing files",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="restrict to specific source_id(s); may be repeated",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="print per-source detail",
    )
    args = parser.parse_args()

    if not SOURCE_DIR.is_dir():
        print(f"source dir not found: {SOURCE_DIR}", file=sys.stderr)
        return 1

    shared = load_shared()

    selected = args.source
    files = sorted(SOURCE_DIR.glob("*.py"))
    if selected:
        wanted = set(selected)
        files = [f for f in files if f.stem in wanted]
        missing = wanted - {f.stem for f in files}
        for m in missing:
            print(f"warning: --source {m!r} not found", file=sys.stderr)

    totals = {
        "scanned": 0,
        "skipped_no_dicts": 0,
        "migrated": 0,
        "parse_errors": 0,
        "translations_dropped_dry": 0,
        "translations_kept": 0,
        "descriptions_dropped_dry": 0,
        "descriptions_kept": 0,
    }
    parse_errors: list[tuple[str, str]] = []
    manual_review: list[tuple[str, list[str]]] = []

    for py_path in files:
        totals["scanned"] += 1
        stats = migrate_one(py_path, shared, dry_run=args.dry_run)
        if "error" in stats:
            totals["parse_errors"] += 1
            parse_errors.append((stats["source_id"], stats["error"]))
            continue
        if stats.get("skipped"):
            totals["skipped_no_dicts"] += 1
            continue
        totals["migrated"] += 1
        totals["translations_dropped_dry"] += (
            stats["translations_total"] - stats["translations_kept"]
        )
        totals["translations_kept"] += stats["translations_kept"]
        totals["descriptions_dropped_dry"] += (
            stats["descriptions_total"] - stats["descriptions_kept"]
        )
        totals["descriptions_kept"] += stats["descriptions_kept"]
        if stats.get("manual_review"):
            manual_review.append((stats["source_id"], stats["manual_review"]))
        if args.verbose:
            print(
                f"{stats['source_id']:50s} "
                f"PT {stats['translations_kept']}/{stats['translations_total']} "
                f"PD {stats['descriptions_kept']}/{stats['descriptions_total']} "
                f"langs={','.join(stats['languages_with_residue']) or '-'}"
                + (
                    f"  MANUAL: {','.join(stats['manual_review'])}"
                    if stats.get("manual_review")
                    else ""
                )
            )

    print()
    print("=" * 60)
    for k, v in totals.items():
        print(f"{k:35s} {v}")

    if manual_review:
        print()
        print(
            f"MANUAL REVIEW: {len(manual_review)} file(s) had non-literal dicts "
            "left in place. Migrate by hand:"
        )
        for source_id, names in manual_review:
            print(f"  {source_id}: {', '.join(names)}")

    if parse_errors:
        print()
        print(f"PARSE ERRORS ({len(parse_errors)}):")
        for source_id, err in parse_errors:
            print(f"  {source_id}: {err}")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
