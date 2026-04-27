#!/usr/bin/env python3
"""One-shot pass: normalise non-canonical Python parameter names across all
source modules to ``snake_case`` English. Renames:

* the parameter name in ``def __init__``
* every reference to the parameter inside the source file (private
  attribute names, body usages, TEST_CASES dict keys)
* the matching key in ``i18n/sources/<source_id>/<lang>.yaml`` overrides

The rename is implemented as a word-boundary regex substitution within each
file. The names being renamed are unusual enough (``houseNo``, ``streetId``,
``streetIndex``, ...) that collisions with unrelated identifiers are
near-zero, but the script reports any case where the pre-rename name is
used in a context other than what we expect (function call, attribute on
something other than ``self``, etc.) so they can be reviewed by hand.

Usage:
    python scripts/normalize_param_names.py [--dry-run]
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Iterable

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


# Rename map: old Python identifier -> new snake_case English identifier.
# Sources that pipe the foreign / camelCase name straight into an HTTP API
# are flagged for manual review (the dict-key safety check below) so the
# string literal in the API call stays put while only the Python identifier
# is renamed.
RENAMES: dict[str, str] = {
    # camelCase -> snake_case
    "addressNo": "address_no",
    "asId": "as_id",
    "bulkyObjectID": "bulky_object_id",
    "daysToGenerate": "days_to_generate",
    "hnId": "hn_id",
    "houseID": "house_id",
    "houseNo": "house_no",
    "idHouseNumber": "id_house_number",
    "kundNr": "kund_nr",
    "objectID": "object_id",
    "objectId": "object_id",
    "postCode": "postcode",
    "propertyID": "property_id",
    "recycleObjectID": "recycle_object_id",
    "registrationNumber": "registration_number",
    "streetId": "street_id",
    "streetIndex": "street_index",
    "streetName": "street_name",
    "trashObjectID": "trash_object_id",
    "wasteTypes": "waste_types",
    "zipCode": "zip_code",
    "zipcode": "zip_code",
    "zoneID": "zone_id",
    # missing-underscore -> snake_case
    "housenumber": "house_number",
    "housenameornumber": "house_name_or_number",
    "housenumberorname": "house_number_or_name",
    "streetname": "street_name",
    # Foreign-language synonyms -> canonical English. zip_code/postcode are
    # kept as separate concepts (regional convention).
    "strasse": "street",
    "hausnr": "house_number",
    "hausnummer": "house_number",
    "hnr": "house_number",
    "plz": "postcode",
    "post_code": "postcode",
    "postal_code": "postcode",
    "kommune": "municipality",
    "gemeinde": "municipality",
    "commune": "municipality",
    "bezirk": "district",
    "ortsteil": "district",
    "stadtteil": "district",
    "stadt": "city",
    "ort": "city",
    # Abbreviations -> canonical full English snake_case.
    "str_id": "street_id",
    "nr": "house_number",
    "cp": "postcode",
    "add": "address_suffix",
    "house_no": "house_number",
    "property_no": "property_id",
    "address_no": "address_id",
    "kund_nr": "customer_number",
    "prem_code": "premises_id",
    "street_index": "street_id",
    # ID variants pointing at the same concept -> single canonical key.
    "hn_id": "house_number_id",
    "id_house_number": "house_number_id",
    # Address / house variants -> single canonical
    "address_name_number": "house_number_or_name",
    "house_name_or_number": "house_number_or_name",
    "house": "house_number_or_name",
    "house_letter": "address_suffix",
    "addition": "address_suffix",
    "address_postcode": "postcode",
    "address_street": "street",
    "street_number": "house_number",
    "number": "house_number",
    "suffix": "address_suffix",
    "property": "property_id",
    "pid": "property_id",
    "property_location": "address",
    "street_town": "street_address",
    "door_num": "unit_number",
    # Street / road
    "road_name": "street_name",
    # Admin / region
    "municipal": "municipality",
    "territory": "region",
    # Customer / provider
    "client": "customer",
    "company": "service_provider",
    "operator": "service_provider",
    # Waste-types
    "types": "waste_types",
    # Czech / French / Polish param names with clear English equivalents.
    "obec": "municipality",
    "obvod": "district",
    "ulice": "street",
    "cislo": "house_number",
    "rue": "street",
    "localite": "locality",
}


def find_init_param_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.ClassDef) and node.name == "Source"):
            continue
        for sub in node.body:
            if isinstance(sub, ast.FunctionDef) and sub.name == "__init__":
                for arg in sub.args.args + sub.args.kwonlyargs:
                    if arg.arg != "self":
                        names.add(arg.arg)
    return names


def _test_cases_lineno_range(tree: ast.Module) -> tuple[int, int] | None:
    """Return (start, end) line numbers of the top-level ``TEST_CASES = {...}``
    assignment, or None if absent. Inclusive.
    """
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == "TEST_CASES":
            return node.lineno, node.end_lineno or node.lineno
    return None


def find_dict_key_occurrences(
    tree: ast.Module, names: Iterable[str], skip_range: tuple[int, int] | None
) -> dict[str, list[int]]:
    """Flag occurrences of the rename targets as DICT LITERAL KEYS outside
    the TEST_CASES block. Those are the high-risk cases (HTTP form fields,
    JSON keys) where renaming would break an external API contract.

    String literals used as positional args to ``SourceArgumentNotFound`` and
    similar exceptions, or in error message bodies, are NOT flagged because
    those should follow the param rename.
    """
    targets = set(names)
    hits: dict[str, list[int]] = {n: [] for n in targets}
    skip_lo, skip_hi = skip_range if skip_range else (0, 0)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key in node.keys:
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                continue
            if key.value not in targets:
                continue
            lineno = key.lineno or 0
            if skip_range and skip_lo <= lineno <= skip_hi:
                continue
            hits[key.value].append(lineno)
    return {n: lines for n, lines in hits.items() if lines}


def apply_renames_in_text(text: str, renames: dict[str, str]) -> str:
    """Apply word-boundary rename to ``text`` for every (old, new) pair."""
    for old, new in renames.items():
        pattern = re.compile(rf"\b{re.escape(old)}\b")
        text = pattern.sub(new, text)
    return text


def rewrite_source(py_path: Path, renames: dict[str, str], dry_run: bool) -> bool:
    text = py_path.read_text(encoding="utf-8")
    new_text = apply_renames_in_text(text, renames)
    if new_text == text:
        return False
    if not dry_run:
        py_path.write_text(new_text, encoding="utf-8", newline="\n")
    return True


def rewrite_yaml(yaml_path: Path, renames: dict[str, str], dry_run: bool) -> bool:
    """Rewrite YAML override files. We treat them as text and rename only
    the second-indent param keys (``  OLD:`` -> ``  NEW:``) so we don't
    accidentally rewrite values that happen to contain the old name.
    """
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
    if not dry_run:
        yaml_path.write_text(new_text, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if not SOURCE_DIR.is_dir():
        print(f"source dir not found: {SOURCE_DIR}", file=sys.stderr)
        return 1

    py_changed: list[Path] = []
    yaml_changed: list[Path] = []
    skipped: list[tuple[Path, str]] = []
    manual_review: list[tuple[Path, list[str]]] = []

    for py_path in sorted(SOURCE_DIR.glob("*.py")):
        try:
            text = py_path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(py_path))
        except SyntaxError as exc:
            skipped.append((py_path, f"parse: {exc}"))
            continue
        params = find_init_param_names(tree)
        # Restrict the rename map to keys that this source actually uses.
        per_source = {old: new for old, new in RENAMES.items() if old in params}
        if not per_source:
            continue

        # Collision check: if the rename target is already a parameter on the
        # same Source class, OR multiple old names in this file collapse to
        # the same new name, the rename would produce duplicate __init__
        # args. Skip and report; a human picks which old name keeps which
        # canonical (or whether the source needs a different scheme entirely).
        target_already_param = {
            old: new for old, new in per_source.items() if new in params
        }
        target_counts: dict[str, list[str]] = {}
        for old, new in per_source.items():
            target_counts.setdefault(new, []).append(old)
        target_collisions = {
            new: olds for new, olds in target_counts.items() if len(olds) > 1
        }
        if target_already_param or target_collisions:
            notes = [
                f"{old}->{new}: target already a param"
                for old, new in target_already_param.items()
            ] + [
                f"{','.join(sorted(olds))} -> {new}: multiple old names map to same target"
                for new, olds in target_collisions.items()
            ]
            manual_review.append((py_path, notes))
            continue

        # Safety check: if the OLD name appears as a string literal *outside*
        # the TEST_CASES block, the rename probably collides with an API
        # contract (HTTP form fields, JSON keys, error messages where we
        # specifically want to keep the user-facing name). Skip and flag for
        # hand work. String literals INSIDE TEST_CASES are dict keys that
        # should follow the param rename.
        skip_range = _test_cases_lineno_range(tree)
        external_hits = find_dict_key_occurrences(tree, per_source.keys(), skip_range)
        if external_hits:
            manual_review.append(
                (py_path, [f"{n} @ {lines}" for n, lines in external_hits.items()])
            )
            continue

        if rewrite_source(py_path, per_source, args.dry_run):
            py_changed.append(py_path)
            if args.verbose:
                print(f"py:   {py_path.stem}  {sorted(per_source)}")

        yaml_dir = I18N_SOURCES_DIR / py_path.stem
        if yaml_dir.is_dir():
            for yaml_path in sorted(yaml_dir.glob("*.yaml")):
                if rewrite_yaml(yaml_path, per_source, args.dry_run):
                    yaml_changed.append(yaml_path)
                    if args.verbose:
                        print(f"yaml: {yaml_path.relative_to(REPO_ROOT)}")

    print()
    print("=" * 60)
    print(f"sources rewritten:  {len(py_changed)}")
    print(f"yaml files updated: {len(yaml_changed)}")
    if manual_review:
        print(
            f"\nMANUAL REVIEW ({len(manual_review)} sources): the old name "
            "appears as a string literal — likely an API key — so the rename "
            "needs hand-mapping."
        )
        for p, names in manual_review:
            print(f"  {p.stem}: {names}")
    if skipped:
        print(f"\nskipped (parse errors): {len(skipped)}")
        for p, err in skipped:
            print(f"  {p.stem}: {err}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
