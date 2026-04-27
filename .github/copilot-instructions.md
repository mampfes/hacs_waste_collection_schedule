# GitHub Copilot Instructions

See [`AGENTS.md`](../AGENTS.md) for the full agent guide. Quick summary:

## Adding or modifying a waste collection source

- Source modules live at
  `custom_components/waste_collection_schedule/waste_collection_schedule/source/<id>.py`
  and must export `TITLE`, `URL`, `TEST_CASES`, and a `Source` class
  with a `fetch()` method returning `list[Collection]`.

- **Do not add `PARAM_TRANSLATIONS` or `PARAM_DESCRIPTIONS` dicts** —
  argument labels/descriptions live in YAML next to the source at
  `<id>.i18n/<lang>.yaml`. For common parameter names
  (`street`, `city`, `postcode`, `house_number`, `uprn`, …) the
  shared registry at
  `custom_components/waste_collection_schedule/i18n/shared/<lang>.yaml`
  resolves them automatically; no per-source YAML is needed in that
  case. `tests/test_i18n.py` blocks the legacy dicts.

- Use `SourceArgumentNotFound`, `SourceArgumentRequired`, etc.
  from `waste_collection_schedule.exceptions` for raised errors —
  not hand-written English `Exception("...")`.

- Don't edit auto-generated files (`README.md`, `info.md`,
  `sources.json`, `source_metadata.json`, `translations/*.json`,
  `doc/ics/*.md`). Run `python update_docu_links.py` from the repo
  root after modifying sources to regenerate them.

- New sources need a manual `doc/source/<id>.md` (the generator does
  not create it).

## Reference docs

- [`doc/contributing_source.md`](../doc/contributing_source.md) —
  dedicated source guide
- [`doc/contributing_ics.md`](../doc/contributing_ics.md) — ICS
  source guide (preferred when the provider has a public ICS feed)
- [`custom_components/waste_collection_schedule/i18n/README.md`](../custom_components/waste_collection_schedule/i18n/README.md) —
  i18n catalog and override layout
