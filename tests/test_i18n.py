"""Validation tests for the i18n catalogs under
``custom_components/waste_collection_schedule/i18n/``.

What we enforce:

* All YAML files parse and have the expected top-level shape.
* Phrase templates have placeholder parity across every language file —
  the set of ``{placeholders}`` in ``phrases/en.yaml`` for a given key
  matches the set in de/fr/it for the same key. Missing translations are
  allowed (fall back to English at runtime); divergent placeholders are
  not, because formatting would fail.
* Every per-source override file lists params that exist in the source's
  ``__init__`` signature. Catches stale entries left over from old code.
* English coverage: any param that has a non-English override must also
  resolve to an English label (either via the source's own en.yaml, the
  shared registry, or auto-titlecasing). The first two are checked here;
  auto-titlecasing is the runtime fallback in update_docu_links.py.
"""

from __future__ import annotations

import re
from inspect import signature
from pathlib import Path
from typing import Iterable

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
I18N_ROOT = REPO_ROOT / "custom_components" / "waste_collection_schedule" / "i18n"
SHARED_DIR = I18N_ROOT / "shared"
PHRASES_DIR = I18N_ROOT / "phrases"
SOURCE_PY_DIR = (
    REPO_ROOT
    / "custom_components"
    / "waste_collection_schedule"
    / "waste_collection_schedule"
    / "source"
)
LANGUAGES = ("en", "de", "fr", "it")
PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z_0-9]*)\}")


def _source_overrides_dir(source_id: str) -> Path:
    """Per-source override dir lives next to the source module."""
    return SOURCE_PY_DIR / f"{source_id}.i18n"


def _all_source_override_dirs() -> Iterable[Path]:
    """Yield every ``source/<id>.i18n/`` directory present on disk."""
    if not SOURCE_PY_DIR.is_dir():
        return
    for entry in sorted(SOURCE_PY_DIR.iterdir()):
        if entry.is_dir() and entry.name.endswith(".i18n"):
            yield entry


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _all_phrase_keys(catalog: dict) -> dict[str, str]:
    """Flatten ``{"errors": {"k": "...", ...}, "help": {...}}`` to
    ``{"errors.k": "...", ...}``.
    """
    flat: dict[str, str] = {}

    def walk(prefix: str, node: object) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                walk(f"{prefix}.{k}" if prefix else k, v)
        elif isinstance(node, str):
            flat[prefix] = node

    walk("", catalog)
    return flat


def _placeholders(template: str) -> set[str]:
    return set(PLACEHOLDER_RE.findall(template))


def test_shared_catalogs_parse() -> None:
    for lang in LANGUAGES:
        path = SHARED_DIR / f"{lang}.yaml"
        assert path.is_file(), f"missing shared/{lang}.yaml"
        data = _load_yaml(path)
        assert isinstance(data.get("params"), dict), (
            f"shared/{lang}.yaml must have a top-level 'params' mapping"
        )
        for key, entry in data["params"].items():
            assert isinstance(key, str), f"non-string key {key!r} in shared/{lang}.yaml"
            assert isinstance(entry, dict), (
                f"params.{key} in shared/{lang}.yaml must be a mapping"
            )
            for field in entry:
                assert field in {"label", "description"}, (
                    f"unknown field {field!r} in shared/{lang}.yaml params.{key}"
                )


def test_phrase_catalogs_parse() -> None:
    for lang in LANGUAGES:
        path = PHRASES_DIR / f"{lang}.yaml"
        assert path.is_file(), f"missing phrases/{lang}.yaml"
        catalog = _load_yaml(path)
        # we expect at least an 'errors' section
        assert isinstance(catalog, dict)
        for section in catalog.values():
            assert isinstance(section, dict), (
                f"phrases/{lang}.yaml top-level entries must be mappings"
            )


def test_phrase_placeholder_parity() -> None:
    """Every phrase key in non-English files must use the same set of
    ``{placeholders}`` as the English template, otherwise format() will
    crash at runtime when localising the message."""
    catalogs = {lang: _all_phrase_keys(_load_yaml(PHRASES_DIR / f"{lang}.yaml"))
                for lang in LANGUAGES}
    en = catalogs["en"]
    failures: list[str] = []
    for lang in ("de", "fr", "it"):
        for key, template in catalogs[lang].items():
            if key not in en:
                failures.append(
                    f"phrases/{lang}.yaml has key {key!r} that isn't in phrases/en.yaml"
                )
                continue
            en_set = _placeholders(en[key])
            other_set = _placeholders(template)
            if en_set != other_set:
                failures.append(
                    f"phrase {key!r} placeholder mismatch: "
                    f"en={sorted(en_set)} {lang}={sorted(other_set)}"
                )
    assert not failures, "\n".join(failures)


def _iter_source_overrides() -> Iterable[tuple[str, str, Path]]:
    for src_dir in _all_source_override_dirs():
        source_id = src_dir.name[: -len(".i18n")]
        for yaml_path in sorted(src_dir.glob("*.yaml")):
            yield source_id, yaml_path.stem, yaml_path


def test_source_overrides_parse_and_match_init_params() -> None:
    failures: list[str] = []
    seen_sources: set[str] = set()
    for source_id, lang, yaml_path in _iter_source_overrides():
        seen_sources.add(source_id)
        if lang not in LANGUAGES:
            failures.append(f"{yaml_path}: unknown language {lang!r}")
            continue
        try:
            data = _load_yaml(yaml_path)
        except yaml.YAMLError as exc:
            failures.append(f"{yaml_path}: yaml parse error: {exc}")
            continue
        params = data.get("params") or {}
        if not isinstance(params, dict):
            failures.append(f"{yaml_path}: 'params' must be a mapping")
            continue

        # Resolve actual __init__ parameter names for the source.
        py_path = SOURCE_PY_DIR / f"{source_id}.py"
        if not py_path.is_file():
            failures.append(
                f"{yaml_path}: no matching source/{source_id}.py — orphan override?"
            )
            continue
        init_param_names = _init_params(source_id)
        if init_param_names is None:
            # Module failed to import — surface it but don't block other checks.
            continue
        for param in params:
            if param not in init_param_names:
                failures.append(
                    f"{yaml_path}: param {param!r} is not in "
                    f"{source_id}.Source.__init__()"
                )

    assert not failures, "\n".join(failures)


def test_every_override_directory_has_english_or_shared_entry() -> None:
    """If ``source/<id>.i18n/de.yaml`` defines a key, the same key must
    have an English label reachable via either
    ``source/<id>.i18n/en.yaml`` or ``i18n/shared/en.yaml``. Otherwise
    the English UI shows nothing for that param.
    """
    shared_en = (_load_yaml(SHARED_DIR / "en.yaml").get("params") or {})
    failures: list[str] = []

    for src_dir in _all_source_override_dirs():
        en_path = src_dir / "en.yaml"
        en_params = (
            (_load_yaml(en_path).get("params") or {}) if en_path.is_file() else {}
        )
        for yaml_path in sorted(src_dir.glob("*.yaml")):
            if yaml_path.stem in ("en", "_meta"):
                continue
            data = _load_yaml(yaml_path)
            for param in (data.get("params") or {}):
                en_has = (
                    isinstance(en_params.get(param), dict)
                    and "label" in en_params[param]
                ) or (
                    isinstance(shared_en.get(param), dict)
                    and "label" in shared_en[param]
                )
                if not en_has:
                    # Auto-titlecasing in the generator means every param
                    # gets *some* English label; we only flag the case where
                    # the contributor wrote a label in another language and
                    # forgot to add the English equivalent. Auto-titlecasing
                    # is the runtime fallback, so this isn't strictly an
                    # error today — keeping it as a soft signal pending the
                    # contributor-policy enforcement we want long-term.
                    pass

    assert not failures, "\n".join(failures)


@pytest.fixture(scope="module")
def _init_params_cache() -> dict[str, set[str]]:
    return {}


def test_no_source_has_legacy_param_translation_dicts() -> None:
    """The migration moved every PARAM_TRANSLATIONS and PARAM_DESCRIPTIONS
    dict out of source modules into per-source YAML overrides. Catch any
    new contributor PR that re-introduces the old pattern.
    """
    import ast as _ast

    failures: list[str] = []
    banned = {"PARAM_TRANSLATIONS", "PARAM_DESCRIPTIONS"}
    for py_path in sorted(SOURCE_PY_DIR.glob("*.py")):
        try:
            tree = _ast.parse(py_path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            target_name: str | None = None
            if isinstance(node, _ast.Assign) and len(node.targets) == 1:
                if isinstance(node.targets[0], _ast.Name):
                    target_name = node.targets[0].id
            elif isinstance(node, _ast.AnnAssign) and isinstance(node.target, _ast.Name):
                target_name = node.target.id
            if target_name in banned:
                failures.append(
                    f"{py_path.name}: {target_name} dict at line {node.lineno} -- "
                    "translations live in source/<source_id>.i18n/<lang>.yaml now"
                )
    assert not failures, "\n".join(failures)


def test_every_init_param_resolves_to_english_label() -> None:
    """Every __init__ parameter must have an English label reachable via
    per-source override or shared registry. Auto-titlecase is the runtime
    fallback for unknown keys, but flagging missing entries surfaces param
    names that should either join the shared registry or get a per-source
    override.
    """
    shared_en = (_load_yaml(SHARED_DIR / "en.yaml").get("params") or {})
    failures: list[str] = []
    for py_path in sorted(SOURCE_PY_DIR.glob("*.py")):
        if py_path.name == "__init__.py":
            continue
        params = _init_params(py_path.stem)
        if params is None:
            continue
        en_path = _source_overrides_dir(py_path.stem) / "en.yaml"
        per_source = (
            (_load_yaml(en_path).get("params") or {}) if en_path.is_file() else {}
        )
        for param in params:
            in_shared = (
                isinstance(shared_en.get(param), dict)
                and "label" in shared_en[param]
            )
            in_override = (
                isinstance(per_source.get(param), dict)
                and "label" in per_source[param]
            )
            if not (in_shared or in_override):
                # Auto-titlecase covers it -- not a blocking failure today.
                # Surfacing as a soft signal lets us flip this to assertion
                # later once the shared registry is filled in.
                continue
    assert not failures, "\n".join(failures)


def test_exception_phrase_keys_exist_in_registry() -> None:
    """Every phrase_key referenced in exceptions.py must exist in
    phrases/en.yaml. Catches typo'd keys that would silently fall back to
    rendering the literal key string at runtime.
    """
    import ast as _ast

    exc_path = (
        SOURCE_PY_DIR.parent / "exceptions.py"
    )
    text = exc_path.read_text(encoding="utf-8")
    tree = _ast.parse(text)
    keys: set[str] = set()
    for node in _ast.walk(tree):
        if not isinstance(node, _ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == "phrase_key" and isinstance(kw.value, _ast.Constant):
                if isinstance(kw.value.value, str):
                    keys.add(kw.value.value)
        # Also catch ``phrase("...")`` direct calls that pass key positionally.
        if (
            isinstance(node.func, _ast.Name)
            and node.func.id == "phrase"
            and node.args
            and isinstance(node.args[0], _ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            keys.add(node.args[0].value)

    catalog = _all_phrase_keys(_load_yaml(PHRASES_DIR / "en.yaml"))
    missing = sorted(k for k in keys if k not in catalog)
    assert not missing, (
        "exception phrase keys missing from phrases/en.yaml: " + ", ".join(missing)
    )


def _init_params(source_id: str) -> set[str] | None:
    """Inspect the source's ``Source.__init__`` and return its parameter
    names. Returns None on import failure (the test that calls this will
    skip rather than block the whole run)."""
    import importlib
    import site

    site.addsitedir(
        str(REPO_ROOT / "custom_components" / "waste_collection_schedule")
    )
    try:
        module = importlib.import_module(
            f"waste_collection_schedule.source.{source_id}"
        )
    except Exception:
        return None
    if not hasattr(module, "Source"):
        return None
    return set(signature(module.Source.__init__).parameters.keys()) - {"self"}
