# CLAUDE.md

Guidance for [Claude Code](https://claude.com/claude-code) in this repository (other AI assistants welcome). This file holds the binding rules only. Rationale, examples and the full component catalogue live in `doc/contributing_source.md` (sources) and `doc/versioning.md` (releases): read the relevant section when you need detail, not the whole file.

## Role

Unless it is clear from the first message or `CLAUDE.local.md`, ask once:

> "Are you a contributor working on a Pull Request, or a maintainer with write access to the upstream repo?"

| Role | Commands | Agents |
|---|---|---|
| Contributor (works in a fork) | `/new-source` | `source-investigator`, `source-implementer` |
| Maintainer (upstream write access) | `/review-pr`, `/review-issue`, `/cleanup`, `/release` | `pr-reviewer`, `pr-executor`, `issue-triager`, `issue-executor`, `repo-cleanup`, `release-manager` |

Personal overrides go in `CLAUDE.local.md` and `.claude/settings.local.json` (both gitignored); load them when present.

## Project

Home Assistant (HACS) custom component fetching waste collection schedules from ~600 providers, configured via YAML or the UI.

- `custom_components/waste_collection_schedule/`: HA layer (config flow, sensors, calendar, services).
- `custom_components/waste_collection_schedule/waste_collection_schedule/`: standalone core library, importable as `waste_collection_schedule`: `source/` (one module per provider), `service/` (shared platform components), `source_shell.py` (customisation, fetch lifecycle), `wizard/`.
- `Collection(date, t, icon=None, picture=None)` is one collection event.

## Commands

```bash
python -m pytest tests/                              # offline CI suite (pytest.ini python_files is an allowlist)
python -m pytest tests/test_source_components.py -q  # structure checks: run after every source change
python tests/record_fixtures.py <module>             # record cassettes for a pipeline source
cd custom_components/waste_collection_schedule/waste_collection_schedule/test && python test_sources.py -s <module> -l  # live test
ruff check --fix <file> && ruff format <file>
pre-commit run --all-files  # ruff, mypy, pyright, codespell, bandit, pyupgrade, yamlfmt; use the pinned hooks, not bare tools
```

## Source rules

Two styles; the guide is `doc/contributing_source.md`.

1. **`BaseSource` pipeline (all new sources).** Class attributes only: metadata, `PARAMS` (factories from `config_params`), `WASTE_TYPES`, and the `retrieve` / `parse` / `preprocess` / `transform` steps (or `classify()`). No `__init__`, no `fetch()`, no `ICON_MAP`, no manual date parsing. Examples: `kwinana_wa_gov_au.py`, `koppl_at.py`, `reading_gov_uk.py`.
2. **Legacy module-level** (~600 sources, still supported): module-level metadata plus `Source.__init__(**kwargs)` and `fetch() -> list[Collection]`. A bug fix does not require conversion.

Required metadata (class attrs for pipeline, module-level for legacy): `TITLE`, `DESCRIPTION`, `URL`, `COUNTRY`, `TEST_CASES` (non-empty). Strongly encouraged: `SOURCE_CODEOWNERS = ["@handle"]` (ICS YAML: `codeowners:`).

- **`COUNTRY`**: lowercase ISO 3166-1 code from `COUNTRYCODES` in `update_docu_links.py`. UK is `"uk"` (not `"gb"`), Canada `"ca"`, Slovenia `si`. An invalid value silently drops the source from all listings.
- **Languages**: ISO 639-1 (Slovenian is `sl`, not `si`). Allowed keys: `LANGUAGES` in `update_docu_links.py` (currently `en de it fr nl sl da`). For any other language, strip it from the PR and open a separate issue `Add <lang> (xx) language support to PARAM_TRANSLATIONS allowlist`. A language is only added to `LANGUAGES` together with `waste_types.SUPPORTED_LANGUAGES` and complete translations (`waste_types` names, `field_terms` labels, `default_translations.py`).
- **Pipeline-only rules (gated in `tests/test_new_architecture.py`)**:
  - Declare `WASTE_TYPES` explicitly as what the cassette replay produces (`[]` only for a bare transformer with no `type_value_map`).
  - One cassette per `TEST_CASES` entry under `tests/fixtures/<module>/`, named by the slugged case key. The backlogs `SOURCES_AWAITING_CASSETTE` / `CASES_AWAITING_CASSETTE` are debt registers: never add to them, delete a line when you record it. Lower `FALLBACK_BUDGET` in `tests/test_offline_fixtures.py` when re-recording.
  - Reuse, don't define: no `Retriever`/`Parser` subclass, step override, or module-level function issuing the provider's HTTP inside a source module. Put the behaviour in a shared component under `service/` (or the retrievers/parsers modules). Never add a source to `SOURCE_LOCAL_STEP_EXCEPTIONS` or `SOURCES_HAND_ROLLING_RETRIEVAL`.
  - Multi-provider coverage via `REGIONS`; a large registry goes in `doc/regions/<source>.yaml` via `regions.from_yaml()`. That is build-time only (`doc/` is not shipped in a HACS install, so `from_yaml()` yields `[]` at runtime): a registry the source needs *while fetching* must stay in Python. Never `EXTRA_INFO`, `PARAM_TRANSLATIONS`, `PARAM_DESCRIPTIONS` or `HOW_TO_GET_ARGUMENTS_DESCRIPTION` (labels come from `field_terms.py`; guidance goes in `HOWTO`).
  - Use `RAISE_ON_EMPTY = True` on address/lookup sources.
  - In any new tool or gate, test pipeline membership with `issubclass(Source, BaseSource)`, never `PARAMS` truthiness (`PARAMS = ()` is falsy).
- **Legacy-only**: `ICON_MAP` values must be `Icons` enum members (`waste_collection_schedule/icons.py`), never raw `"mdi:..."`; don't extend the enum in a source PR. Every new legacy source needs a hand-written `doc/source/<id>.md`.
- **Exceptions**: `SourceArgumentNotFound` / `SourceArgumentNotFoundWithSuggestions` (from `waste_collection_schedule.exceptions`), never a bare `Exception`.
- **403 / Cloudflare**: use `curl_cffi` (`requests.Session(impersonate="chrome")`; the pipeline default retriever already does).

**Never:**
- hardcoded dates or schedules (fetch live);
- login-required endpoints;
- `if __name__ == "__main__":` blocks or dummy params like `_`;
- a new source for a provider already on a shared platform (ICS YAML incl. `recollect.yaml` and `mein_abfallkalender_online.yaml`, `recyclecoach_com`, `c_trace_de`, and every platform in the guide's "Reusable service platforms" table): check first;
- a dedicated `tests/test_<source>.py`. `TEST_CASES` plus cassettes plus a live `test_sources.py` run is the expected coverage; add one only for logic cases cannot exercise, with network mocked.

## Generated files: never edit, never run `update_docu_links.py`

CI regenerates these after every push to `master`. If a PR diff touches one, revert with `git checkout upstream/<base> -- <file>`, where `<base>` is the PR's target branch (`master` or `release/3.0.0`):

- `README.md`, `info.md`
- `custom_components/waste_collection_schedule/sources.json`, `source_metadata.json`
- `custom_components/waste_collection_schedule/translations/*.json` (only the `config.step.args_*` sections are generated; `options.step.init` is hand-maintained)
- `custom_components/waste_collection_schedule/waste_collection_schedule/translations/*.json`
- `doc/ics/*.md`, and `doc/source/<id>.md` for pipeline sources

Hand-edited: source modules, `doc/source/<id>.md` for legacy sources, `doc/source/ics.md` and `static.md`, `doc/ics/yaml/*.yaml` (list further providers under `regions:`, not the old `extra_info:`; a `howto` may also list per-provider service URLs, which are maintained separately from `regions[].url`), `CHANGELOG.md` and `manifest.json` (release time only).

## Git and GitHub

- PRs go from a feature branch to `mampfes/hacs_waste_collection_schedule`. Never commit to `master` (local, origin or upstream), and never push to your fork's `master`.
- **PR target during the 3.0.0 window:** new sources and breaking changes go to `release/3.0.0` (branch from `upstream/release/3.0.0`); non-breaking fixes to existing sources go to `master`.
- Maintainers: always show the exact text of reviews, comments, label changes and closes before posting. Fix minor issues (style, lint, missing doc file) yourself and approve; request changes for substantive ones (hardcoded data, no live API, security, wrong approach).
- Never ask users for their address or identifying data; use existing `TEST_CASES` or public examples.
- After a merge, `/cleanup`.

## Versioning

Strict SemVer (`doc/versioning.md`): patch = fixes/deps/docs, minor = additions and new deprecations, major = breaking. A legacy-to-pipeline migration is **major** (it changes waste-type labels) and is batched into one major, released first as alpha/beta. Deprecations get a runtime warning, a CHANGELOG `Deprecated` entry and a `DEPRECATIONS.md` row, stay for at least two minor releases, and are removed in the next major.
