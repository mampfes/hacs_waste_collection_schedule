# i18n catalogs for waste_collection_schedule

This directory holds all translatable strings used by source modules. Each
language lives in its own YAML file so `pyspelling` can pair each file with
the matching hunspell dictionary (per-language spell checking).

## Layout

```
i18n/
├── shared/
│   ├── en.yaml      canonical reusable param labels + descriptions
│   ├── de.yaml
│   ├── fr.yaml
│   └── it.yaml
├── phrases/
│   ├── en.yaml      reusable error / help templates with {placeholders}
│   ├── de.yaml
│   ├── fr.yaml
│   └── it.yaml
└── sources/
    └── <source_id>/
        ├── en.yaml  per-source override (only when shared isn't enough)
        └── <lang>.yaml
```

## Adding a new source

If your source's `__init__` parameters all use names that appear in
`shared/en.yaml` (`street`, `city`, `house_number`, `postcode`, ...) you
don't need to add anything here — labels and descriptions resolve through
the shared registry automatically.

If your source has a parameter that **isn't** in the shared registry, or
you need different wording, create:

```yaml
# i18n/sources/<source_id>/en.yaml
---
params:
  my_special_param:
    label: My Special Param
    description: Free-text description shown under the field.
```

Required:
- `en.yaml` for any new param the shared registry doesn't cover.
- A `<native_lang>.yaml` if your source's typical user is non-English
  (e.g. a German source should also have `de.yaml`).

## Resolution order

When `update_docu_links.py` builds the per-language `translations/<lang>.json`
that Home Assistant consumes:

1. `i18n/sources/<source_id>/<lang>.yaml` (highest)
2. `i18n/shared/<lang>.yaml`
3. English fallback (`<lang>` -> `en` for the same key)
4. Auto-titlecased Python identifier (`house_number` -> "House Number")

Per-source files only need entries that **override** what shared provides.
Re-stating the shared label is auto-pruned by the redundancy audit
(`tests/test_i18n.py`).

## TITLE / DESCRIPTION / EXTRA_INFO

`TITLE`, `DESCRIPTION`, and `EXTRA_INFO[].title` strings stay in source
modules (they're metadata, not user-facing form labels). For non-English
sources, declare which dictionary should spell-check them via:

```python
TITLE = "Abfallwirtschaft Bad Kreuznach"
TITLE_LANG = "de"          # default "en" if omitted
DESCRIPTION = "Abfuhrkalender für Bad Kreuznach"
DESCRIPTION_LANG = "de"
EXTRA_INFO_LANG = "de"     # for the title strings inside EXTRA_INFO entries
```

`scripts/extract_titles.py` walks every source, buckets these strings by
their `*_LANG` flag, and writes them out for the `titles-*` matrix entries
in `.pyspelling.yml`.

## Phrases (exception messages)

Reusable error / help templates with `{placeholders}` live in
`phrases/<lang>.yaml`. The `SourceArgumentNotFound`, `SourceArgumentRequired`,
etc. classes in `waste_collection_schedule/exceptions.py` carry a
`phrase_key` plus placeholder values; `.message` resolves to English by
default and `.render(lang)` renders in any supported language.

Adding a new shared error pattern:

1. Add the template to `phrases/en.yaml` under `errors:` or `help:`.
2. Add the same key with a translation in `phrases/{de,fr,it}.yaml` —
   the placeholder names must match (e.g. all four files must use `{argument}`
   and `{value}`).
3. The placeholder-parity test (`test_phrase_placeholder_parity`) catches
   mismatches.

## Spell checking

`pyspelling -c .pyspelling.yml` runs in CI and pairs each language's
catalog with the matching hunspell dictionary
(`hunspell-en-us` / `hunspell-de-de` / `hunspell-fr` / `hunspell-it`).

If hunspell flags a legitimate-but-unknown term (place names, council
acronyms, source-specific jargon), add it to the matching wordlist in
`.spelling/<lang>.wordlist`.

## Tests (`tests/test_i18n.py`)

- All YAML files parse and have the expected shape.
- Phrase placeholders are consistent across languages.
- Per-source override params exist in the source's `__init__` signature.
- No source file uses the legacy `PARAM_TRANSLATIONS` /
  `PARAM_DESCRIPTIONS` pattern (catches accidental regressions).
- Every phrase key referenced from `exceptions.py` exists in
  `phrases/en.yaml`.

Run with `pytest tests/test_i18n.py`.
