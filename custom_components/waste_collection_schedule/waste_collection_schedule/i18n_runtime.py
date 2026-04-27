"""Runtime helpers for the i18n catalogs in custom_components/.../i18n/.

Source modules and the translation generator both load translatable strings
through this module instead of inlining English / German / French / Italian
text in Python source. That separation is what makes per-language spell
checking with hunspell tractable: every i18n YAML file contains exactly one
language, so pyspelling can pair it with the matching dictionary.

Public surface (intentionally small):

* ``LANGUAGES`` — the four supported language codes.
* ``load_shared(lang)`` — return the shared registry mapping for a language.
* ``load_phrases(lang)`` — return the phrase template mapping for a language.
* ``load_source_overrides(source_id, lang)`` — return a source's override
  mapping (or an empty dict if the source has no overrides for that language).
* ``phrase(key, *, lang='en', **placeholders)`` — resolve a phrase template,
  format placeholders, fall back to English if the language is missing.
* ``TranslatedError`` — exception base class that carries a phrase key plus
  placeholder values so the display layer can render it in the user's
  Home Assistant UI language.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import yaml

LANGUAGES: tuple[str, ...] = ("en", "de", "fr", "it")
DEFAULT_LANG = "en"

_I18N_ROOT = Path(__file__).resolve().parents[1] / "i18n"
_SOURCE_DIR = Path(__file__).resolve().parent / "source"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        loaded = yaml.safe_load(f)
    return loaded or {}


def _source_overrides_dir(source_id: str) -> Path:
    """Per-source i18n directory living next to the source module."""
    return _SOURCE_DIR / f"{source_id}.i18n"


@lru_cache(maxsize=None)
def load_shared(lang: str) -> dict[str, Any]:
    """Return the shared params/descriptions catalog for one language."""
    return _read_yaml(_I18N_ROOT / "shared" / f"{lang}.yaml")


@lru_cache(maxsize=None)
def load_phrases(lang: str) -> dict[str, Any]:
    """Return the phrase template catalog for one language."""
    return _read_yaml(_I18N_ROOT / "phrases" / f"{lang}.yaml")


@lru_cache(maxsize=None)
def load_source_overrides(source_id: str, lang: str) -> dict[str, Any]:
    """Return a source's per-language override file, or {} if absent.

    Per-source overrides live in ``source/<source_id>.i18n/<lang>.yaml``,
    a sibling of the source module so contributors keep all assets for
    one source in one place.
    """
    return _read_yaml(_source_overrides_dir(source_id) / f"{lang}.yaml")


def shared_languages() -> Iterable[str]:
    """Return the language codes that have any catalog files on disk."""
    seen: set[str] = set()
    for sub in ("shared", "phrases"):
        d = _I18N_ROOT / sub
        if not d.is_dir():
            continue
        for entry in d.iterdir():
            if entry.suffix == ".yaml":
                seen.add(entry.stem)
    return sorted(seen)


def source_ids_with_overrides() -> list[str]:
    """List source_ids that have a sibling ``<source_id>.i18n/`` directory."""
    if not _SOURCE_DIR.is_dir():
        return []
    return sorted(
        p.name[: -len(".i18n")]
        for p in _SOURCE_DIR.iterdir()
        if p.is_dir() and p.name.endswith(".i18n")
    )


def resolve_param(
    source_id: str,
    param: str,
    lang: str,
    *,
    field: str = "label",
) -> str | None:
    """Resolve a parameter's label or description for a language.

    Resolution order: per-source override -> shared registry -> English
    fallback. Returns None when no entry exists in any layer.
    """
    for candidate_lang in (lang, DEFAULT_LANG) if lang != DEFAULT_LANG else (lang,):
        override = load_source_overrides(source_id, candidate_lang)
        entry = (override.get("params") or {}).get(param)
        if isinstance(entry, dict) and field in entry:
            return entry[field]
        shared = load_shared(candidate_lang)
        entry = (shared.get("params") or {}).get(param)
        if isinstance(entry, dict) and field in entry:
            return entry[field]
    return None


def phrase(
    key: str,
    *,
    lang: str = DEFAULT_LANG,
    **placeholders: Any,
) -> str:
    """Resolve a phrase template by dotted key and substitute placeholders.

    Falls back to English when the requested language has no entry, and
    finally to the raw template key if even English is missing — that last
    case indicates a registry bug and is loud enough to be visible in tests.
    """
    template = _lookup_phrase(key, lang) or _lookup_phrase(key, DEFAULT_LANG)
    if template is None:
        return key
    if not placeholders:
        return template
    return template.format(**placeholders)


def _lookup_phrase(key: str, lang: str) -> str | None:
    catalog = load_phrases(lang)
    node: Any = catalog
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    if isinstance(node, str):
        return node
    return None


class TranslatedError(Exception):
    """Exception carrying a phrase key and placeholder values.

    The display layer (config_flow / sensor) reads ``phrase_key`` and
    ``placeholders`` and renders the message in the user's Home Assistant
    locale via ``phrase(self.phrase_key, lang=user_lang, **self.placeholders)``.
    For callers that only access ``str(exc)``, the message is rendered in
    English so log output stays readable without locale context.
    """

    def __init__(self, phrase_key: str, **placeholders: Any) -> None:
        self.phrase_key = phrase_key
        self.placeholders = placeholders
        super().__init__(phrase(phrase_key, lang=DEFAULT_LANG, **placeholders))

    def render(self, lang: str = DEFAULT_LANG) -> str:
        """Render this exception in the requested language."""
        return phrase(self.phrase_key, lang=lang, **self.placeholders)


def clear_caches() -> None:
    """Drop all cached YAML reads. Useful for tests that mutate the catalogs."""
    load_shared.cache_clear()
    load_phrases.cache_clear()
    load_source_overrides.cache_clear()


# Allow tests / scripts to override the i18n root via env var without monkey
# patching the module-level constant.
if env_root := os.environ.get("WCS_I18N_ROOT"):
    _I18N_ROOT = Path(env_root).resolve()
    clear_caches()
