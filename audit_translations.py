#!/usr/bin/env python3
"""Audit PARAM_TRANSLATIONS coverage across waste_collection_schedule source files.

This tool scans every source file under
``custom_components/waste_collection_schedule/waste_collection_schedule/source/``
and classifies its translation coverage against the central
``DEFAULT_PARAM_TRANSLATIONS`` registry defined in ``default_translations.py``.

Addresses issue #5958: a large number of source files have English-only
(or no) ``PARAM_TRANSLATIONS``, which causes raw parameter names to leak
into non-English Home Assistant UIs. Many of the missing entries already
have translations in the central registry and can be auto-filled without
any new translation work.

For each missing ``(language, param)`` pair the tool determines whether:

* the entry already exists in ``DEFAULT_PARAM_TRANSLATIONS`` and can be
  lifted into the file with zero new translation effort, or
* the entry does not exist in the registry and needs a human translation.

Usage::

    # Default terse report, grouped by language
    python3 audit_translations.py

    # Machine-readable JSON envelope
    python3 audit_translations.py --json

    # Suggest a concrete PARAM_TRANSLATIONS block for one file (read-only)
    python3 audit_translations.py --suggest path/to/source/some_source.py

    # Limit to a subset of languages
    python3 audit_translations.py --languages de,fr

    # Exit 1 if any missing entries are found (for CI gates)
    python3 audit_translations.py --strict

    # Run the inline doctests
    python3 -m doctest audit_translations.py -v

The tool is strictly read-only: it never modifies source files.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
from pathlib import Path
from typing import Iterable

DEFAULT_LANGUAGES = ("en", "de", "fr", "it")
SOURCE_SUBPATH = Path(
    "custom_components/waste_collection_schedule/waste_collection_schedule/source"
)
DEFAULT_TRANSLATIONS_FILENAME = "default_translations.py"


def _dict_from_ast(node: ast.AST) -> dict | None:
    """Return ``node`` as a plain ``dict`` if it is a safe literal, else ``None``.

    Only string keys and string values are preserved for the inner
    language dicts. This is intentionally conservative: anything that
    isn't a literal string -> string mapping is skipped so we never claim
    coverage for dynamic structures we can't statically verify.
    """
    if not isinstance(node, ast.Dict):
        return None
    result: dict = {}
    for key_node, val_node in zip(node.keys, node.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            return None
        key = key_node.value
        if isinstance(val_node, ast.Dict):
            inner = _dict_from_ast(val_node)
            if inner is None:
                return None
            result[key] = inner
        elif isinstance(val_node, ast.Constant) and isinstance(val_node.value, str):
            result[key] = val_node.value
        else:
            # Unsupported value shape (e.g. call, name ref). Bail.
            return None
    return result


def extract_param_translations(source: str) -> dict | None:
    """Extract a module-level ``PARAM_TRANSLATIONS`` dict literal from *source*.

    Returns ``None`` if the name is absent or its value isn't a plain
    dict literal we can statically resolve. Raises ``SyntaxError`` if
    *source* is not valid Python — callers are expected to handle it.

    Use :func:`has_param_translations_name` to disambiguate "absent" from
    "present but dynamic".

    >>> extract_param_translations('PARAM_TRANSLATIONS = {"de": {"street": "Stra\u00dfe"}}')
    {'de': {'street': 'Stra\u00dfe'}}
    >>> extract_param_translations('x = 1') is None
    True
    >>> extract_param_translations('PARAM_TRANSLATIONS = some_call()') is None
    True
    """
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PARAM_TRANSLATIONS":
                    return _dict_from_ast(node.value)
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if (
                isinstance(target, ast.Name)
                and target.id == "PARAM_TRANSLATIONS"
                and node.value is not None
            ):
                return _dict_from_ast(node.value)
    return None


def has_param_translations_name(source: str) -> bool:
    """Return True if *source* defines a module-level ``PARAM_TRANSLATIONS`` name.

    Unlike :func:`extract_param_translations` this says nothing about the
    value — it only reports whether the name is assigned at module level.
    Useful for detecting "present but dynamically constructed" cases
    (e.g. ``PARAM_TRANSLATIONS = {**shared, "de": {...}}``).

    Raises ``SyntaxError`` if *source* is not valid Python.

    >>> has_param_translations_name('PARAM_TRANSLATIONS = some_call()')
    True
    >>> has_param_translations_name('x = 1')
    False
    """
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PARAM_TRANSLATIONS":
                    return True
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == "PARAM_TRANSLATIONS":
                return True
    return False


def extract_source_init_params(source: str) -> list[str] | None:
    """Return the parameter names of ``class Source``'s ``__init__``.

    ``self`` is excluded. Returns ``None`` if there is no ``class Source``
    with an ``__init__``. ``*args`` and ``**kwargs`` are skipped. Raises
    ``SyntaxError`` if *source* is not valid Python.

    >>> extract_source_init_params('''
    ... class Source:
    ...     def __init__(self, street, house_number=None):
    ...         pass
    ... ''')
    ['street', 'house_number']
    >>> extract_source_init_params('class Source:\\n    pass') is None
    True
    """
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Source":
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "__init__":
                    args = item.args
                    names: list[str] = []
                    for a in args.posonlyargs + args.args + args.kwonlyargs:
                        if a.arg == "self":
                            continue
                        names.append(a.arg)
                    return names
            return None
    return None


def classify_missing(
    params: Iterable[str],
    existing: dict,
    registry: dict,
    languages: Iterable[str],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Split missing ``(lang, param)`` pairs into auto-resolvable vs new-work.

    *existing* is the file's current ``PARAM_TRANSLATIONS`` (may be empty)
    and *registry* is ``DEFAULT_PARAM_TRANSLATIONS``.

    A pair is auto-resolvable if the param is absent for that language in
    *existing* but present in ``registry[lang]``. Otherwise it's
    needs-new-translation.

    Returns ``(auto_resolvable, needs_new)`` where each is
    ``{lang: sorted_param_list}``.

    >>> reg = {"de": {"street": "Stra\u00dfe"}, "fr": {"street": "Rue"}}
    >>> existing = {"de": {}}
    >>> auto, new = classify_missing(["street", "foo"], existing, reg, ["de", "fr"])
    >>> auto
    {'de': ['street'], 'fr': ['street']}
    >>> new
    {'de': ['foo'], 'fr': ['foo']}
    """
    auto_resolvable: dict[str, list[str]] = {lang: [] for lang in languages}
    needs_new: dict[str, list[str]] = {lang: [] for lang in languages}
    params = list(params)
    for lang in languages:
        have_for_lang = set((existing.get(lang) or {}).keys())
        reg_for_lang = registry.get(lang, {}) or {}
        for param in params:
            if param in have_for_lang:
                continue
            if param in reg_for_lang:
                auto_resolvable[lang].append(param)
            else:
                needs_new[lang].append(param)
        auto_resolvable[lang].sort()
        needs_new[lang].sort()
    return auto_resolvable, needs_new


def load_registry(default_translations_path: Path) -> dict:
    """Import ``DEFAULT_PARAM_TRANSLATIONS`` from the given module file.

    Raises ``RuntimeError`` if the file cannot be imported or does not
    define ``DEFAULT_PARAM_TRANSLATIONS`` — we fail loud rather than
    silently emitting an empty registry, which would misclassify every
    missing entry as "needs new translation".
    """
    spec = importlib.util.spec_from_file_location(
        "_audit_default_translations", str(default_translations_path)
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {default_translations_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "DEFAULT_PARAM_TRANSLATIONS"):
        raise RuntimeError(
            f"{default_translations_path.name} does not define DEFAULT_PARAM_TRANSLATIONS"
        )
    return module.DEFAULT_PARAM_TRANSLATIONS


def audit_file(path: Path, registry: dict, languages: Iterable[str]) -> dict:
    """Audit a single source file. Returns a per-file result dict.

    On read/parse failure the returned dict has ``unparseable: True``
    and an ``error`` field carrying the exact cause (OSError message,
    SyntaxError line + message, or "no Source.__init__ found").
    """
    languages = list(languages)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"path": str(path), "unparseable": True, "error": f"read failed: {exc}"}

    try:
        init_params = extract_source_init_params(text)
        pt = extract_param_translations(text)
        has_pt_name = has_param_translations_name(text)
    except SyntaxError as exc:
        return {
            "path": str(path),
            "unparseable": True,
            "error": f"SyntaxError: {exc.msg} at line {exc.lineno}",
        }

    if init_params is None:
        return {
            "path": str(path),
            "unparseable": True,
            "error": "no Source.__init__ found",
        }

    has_pt = pt is not None
    dynamic_pt = has_pt_name and not has_pt
    existing = pt or {}

    languages_present = [lang for lang in languages if existing.get(lang)]
    languages_missing = [lang for lang in languages if not existing.get(lang)]

    auto_resolvable, needs_new = classify_missing(
        init_params, existing, registry, languages
    )

    return {
        "path": str(path),
        "has_param_translations": has_pt,
        "dynamic_param_translations": dynamic_pt,
        "languages_present": languages_present,
        "languages_missing": languages_missing,
        "params_detected": init_params,
        "auto_resolvable": {k: v for k, v in auto_resolvable.items() if v},
        "needs_new_translation": {k: v for k, v in needs_new.items() if v},
        "unparseable": False,
    }


def scan_sources(source_dir: Path, registry: dict, languages: Iterable[str]) -> list[dict]:
    languages = list(languages)
    results: list[dict] = []
    for path in sorted(source_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        results.append(audit_file(path, registry, languages))

    dynamic = [r["path"] for r in results if r.get("dynamic_param_translations")]
    if dynamic:
        print(
            f"warning: {len(dynamic)} file(s) define PARAM_TRANSLATIONS dynamically "
            f"(e.g. via **merge or a function call) — their coverage cannot be "
            f"statically determined and they are reported as missing. Sample: "
            f"{Path(dynamic[0]).name}",
            file=sys.stderr,
        )
    return results


def build_summary(results: list[dict], languages: Iterable[str]) -> dict:
    """Aggregate per-file results into a summary."""
    languages = list(languages)
    total = len(results)
    coverage = {lang: {"with_entries": 0, "missing": 0} for lang in languages}
    missing_entry_counts = {lang: {"auto": 0, "new": 0, "files": 0} for lang in languages}
    unparseable = 0

    for r in results:
        if r.get("unparseable"):
            unparseable += 1
            continue
        for lang in languages:
            if lang in r["languages_present"]:
                coverage[lang]["with_entries"] += 1
            else:
                coverage[lang]["missing"] += 1
        for lang in languages:
            auto = r["auto_resolvable"].get(lang, [])
            new = r["needs_new_translation"].get(lang, [])
            if auto or new:
                missing_entry_counts[lang]["files"] += 1
            missing_entry_counts[lang]["auto"] += len(auto)
            missing_entry_counts[lang]["new"] += len(new)

    return {
        "total_sources": total,
        "unparseable": unparseable,
        "coverage": coverage,
        "missing_entry_counts": missing_entry_counts,
    }


def format_default_report(results: list[dict], languages: Iterable[str]) -> str:
    languages = list(languages)
    summary = build_summary(results, languages)
    total = summary["total_sources"]
    lines: list[str] = []
    lines.append(f"Translation audit - {total} sources scanned")
    if summary["unparseable"]:
        lines.append(f"  ({summary['unparseable']} unparseable, excluded from details)")
    lines.append("")
    lines.append("Coverage by language:")
    for lang in languages:
        c = summary["coverage"][lang]
        lines.append(
            f"  {lang}: {c['with_entries']:4d} files have entries / "
            f"{c['missing']:4d} missing / {total} total"
        )
    lines.append("")
    lines.append("Missing entries by auto-resolvability:")
    for lang in languages:
        m = summary["missing_entry_counts"][lang]
        total_missing = m["auto"] + m["new"]
        lines.append(
            f"  {lang}: {total_missing} missing entries across {m['files']} files "
            f"({m['auto']} auto-resolvable from registry, {m['new']} need new translation)"
        )
    lines.append("")

    # Top files by auto-resolvable gain.
    gain_rows: list[tuple[str, int, list[str]]] = []
    for r in results:
        if r.get("unparseable"):
            continue
        auto_total = sum(len(v) for v in r["auto_resolvable"].values())
        if auto_total == 0:
            continue
        langs = [lang for lang in languages if r["auto_resolvable"].get(lang)]
        short = Path(r["path"]).name
        gain_rows.append((short, auto_total, langs))
    gain_rows.sort(key=lambda t: (-t[1], t[0]))

    if gain_rows:
        lines.append(
            "Top files by auto-resolvable gain "
            "(fixing these unlocks the most coverage with zero new translation work):"
        )
        for i, (name, count, langs) in enumerate(gain_rows[:15], start=1):
            lines.append(
                f"  {i:2d}. source/{name:<40s} - "
                f"{count:3d} entries auto-resolvable ({', '.join(langs)})"
            )
    else:
        lines.append("No auto-resolvable gains available.")

    return "\n".join(lines) + "\n"


def format_json_report(results: list[dict], languages: Iterable[str]) -> str:
    languages = list(languages)
    summary = build_summary(results, languages)
    envelope = {
        "total_sources": summary["total_sources"],
        "unparseable": summary["unparseable"],
        "languages": list(languages),
        "coverage": summary["coverage"],
        "missing_entry_counts": summary["missing_entry_counts"],
        "files": results,
    }
    return json.dumps(envelope, indent=2, ensure_ascii=False)


class SuggestError(Exception):
    """Raised when ``format_suggestion`` cannot produce output for a file."""


def format_suggestion(path: Path, registry: dict, languages: Iterable[str]) -> str:
    """Return a copy-pasteable PARAM_TRANSLATIONS block for *path*.

    Entries found in the registry are filled in. Missing entries get a
    ``# TODO: translate`` comment with the raw English fallback as
    placeholder so reviewers can see what needs translating.

    Raises :class:`SuggestError` if the file cannot be read, cannot be
    parsed, or has no ``class Source`` with an ``__init__``. Callers
    should surface the error to the user rather than emit a bogus block.
    """
    languages = list(languages)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SuggestError(f"cannot read {path}: {exc}") from exc
    try:
        params = extract_source_init_params(text)
    except SyntaxError as exc:
        raise SuggestError(
            f"SyntaxError in {path}: {exc.msg} at line {exc.lineno}"
        ) from exc
    if params is None:
        raise SuggestError(f"no class Source with __init__ found in {path}")
    existing = extract_param_translations(text) or {}

    out: list[str] = []
    out.append(f"# Suggested PARAM_TRANSLATIONS for {path.name}")
    out.append(f"# Detected __init__ params: {', '.join(params) or '(none)'}")
    out.append("PARAM_TRANSLATIONS = {")
    for lang in languages:
        out.append(f'    "{lang}": {{')
        have = existing.get(lang) or {}
        reg = registry.get(lang, {}) or {}
        for param in params:
            if param in have:
                value = have[param]
                out.append(f'        "{param}": {json.dumps(value, ensure_ascii=False)},')
            elif param in reg:
                value = reg[param]
                out.append(
                    f'        "{param}": {json.dumps(value, ensure_ascii=False)},'
                )
            else:
                # Use the param name as a placeholder; contributor must translate.
                out.append(
                    f'        "{param}": "{param}",  # TODO: translate'
                )
        out.append("    },")
    out.append("}")
    return "\n".join(out) + "\n"


def _resolve_paths(script_path: Path, source_dir: Path | None) -> tuple[Path, Path]:
    root = script_path.parent
    registry_path = root / DEFAULT_TRANSLATIONS_FILENAME
    if source_dir is None:
        source_dir = root / SOURCE_SUBPATH
    return registry_path, source_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit PARAM_TRANSLATIONS coverage across source files and flag which "
            "missing entries can be auto-resolved from DEFAULT_PARAM_TRANSLATIONS. "
            "See issue #5958."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the terse text report.",
    )
    parser.add_argument(
        "--suggest",
        metavar="PATH",
        help=(
            "Print a suggested PARAM_TRANSLATIONS block for the given source file. "
            "Read-only: the file is not modified."
        ),
    )
    parser.add_argument(
        "--languages",
        default=",".join(DEFAULT_LANGUAGES),
        help="Comma-separated languages to audit (default: en,de,fr,it).",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Override the source directory (default: auto-detected relative to this script).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any missing entries are found (useful in CI).",
    )
    args = parser.parse_args(argv)

    script_path = Path(__file__).resolve()
    registry_path, source_dir = _resolve_paths(script_path, args.source_dir)

    if not registry_path.exists():
        print(f"error: cannot find {registry_path}", file=sys.stderr)
        return 2
    if not source_dir.exists():
        print(f"error: cannot find source dir {source_dir}", file=sys.stderr)
        return 2

    languages = [s.strip() for s in args.languages.split(",") if s.strip()]
    registry = load_registry(registry_path)

    if args.suggest:
        target = Path(args.suggest)
        if not target.is_absolute():
            # Try relative to cwd first, then repo root.
            cwd_rel = Path.cwd() / target
            repo_rel = registry_path.parent / target
            target = cwd_rel if cwd_rel.exists() else repo_rel
        if not target.exists():
            print(f"error: file not found: {args.suggest}", file=sys.stderr)
            return 2
        try:
            print(format_suggestion(target, registry, languages), end="")
        except SuggestError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        return 0

    results = scan_sources(source_dir, registry, languages)

    if args.json:
        print(format_json_report(results, languages))
    else:
        print(format_default_report(results, languages), end="")

    if args.strict:
        summary = build_summary(results, languages)
        total_missing = sum(
            m["auto"] + m["new"]
            for m in summary["missing_entry_counts"].values()
        )
        if total_missing:
            return 1
    return 0


def _self_test() -> int:
    """Exercise the pure helpers against inline fixtures. Returns 0 on success."""
    failures: list[str] = []

    fixture_full = '''
class Source:
    def __init__(self, street, house_number):
        pass
PARAM_TRANSLATIONS = {
    "de": {"street": "Stra\u00dfe", "house_number": "Hausnummer"},
}
'''
    params = extract_source_init_params(fixture_full)
    if params != ["street", "house_number"]:
        failures.append(f"init params mismatch: {params}")

    pt = extract_param_translations(fixture_full)
    if pt != {"de": {"street": "Stra\u00dfe", "house_number": "Hausnummer"}}:
        failures.append(f"PARAM_TRANSLATIONS mismatch: {pt}")

    fixture_empty = '''
class Source:
    def __init__(self, custom_arg):
        pass
'''
    params2 = extract_source_init_params(fixture_empty)
    if params2 != ["custom_arg"]:
        failures.append(f"init params (empty) mismatch: {params2}")
    if extract_param_translations(fixture_empty) is not None:
        failures.append("expected None for file with no PARAM_TRANSLATIONS")

    registry = {
        "de": {"street": "Stra\u00dfe"},
        "fr": {"street": "Rue"},
        "it": {},
    }
    auto, new = classify_missing(
        ["street", "custom_arg"], {}, registry, ["de", "fr", "it"]
    )
    if auto != {"de": ["street"], "fr": ["street"], "it": []}:
        failures.append(f"auto mismatch: {auto}")
    if new != {"de": ["custom_arg"], "fr": ["custom_arg"], "it": ["custom_arg", "street"]}:
        failures.append(f"new mismatch: {new}")

    # Non-literal PARAM_TRANSLATIONS must be rejected.
    fixture_dynamic = "PARAM_TRANSLATIONS = default_translations(['street'])\n"
    if extract_param_translations(fixture_dynamic) is not None:
        failures.append("expected None for dynamic PARAM_TRANSLATIONS")

    if failures:
        print("SELF-TEST FAIL:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("self-test ok")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        sys.exit(_self_test())
    sys.exit(main())
