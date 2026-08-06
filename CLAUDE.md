# CLAUDE.md

Guidance for [Claude Code](https://claude.com/claude-code) when working in this repository. Other AI coding assistants are welcome to read this file too.

## Role detection — read this first

At the start of a session, determine who you are helping. The two roles see this codebase very differently:

- **Contributor**: implementing a new source, fixing a bug, or otherwise preparing changes for a Pull Request. No write access to the upstream repo (`mampfes/hacs_waste_collection_schedule`). Works in a fork.
- **Maintainer**: has write access to the upstream repo. Reviews and merges PRs, triages issues, prepares releases. Can push to contributor branches when "allow maintainer edits" is enabled.

If it isn't already clear from the user's first message or from a `CLAUDE.local.md` file, **ask once** at the start of the session:

> "Are you a contributor working on a Pull Request, or a maintainer with write access to the upstream repo?"

Use the answer to choose which slash commands and agents apply:

| Role | Primary commands | Primary agents |
|---|---|---|
| Contributor | `/new-source` | `source-investigator`, `source-implementer` |
| Maintainer | `/review-pr`, `/review-issue`, `/cleanup` | `pr-reviewer`, `pr-executor`, `issue-triager`, `issue-executor`, `repo-cleanup` |

Maintainers may keep personal overrides (permission allowlists, hooks, draft templates) in `.claude/settings.local.json` and `CLAUDE.local.md`, both gitignored. Load those when present.

---

## Project overview

**hacs_waste_collection_schedule** is a Home Assistant (HACS) custom component that retrieves waste/bin collection schedules from ~600 service providers worldwide. It supports both YAML and UI-based configuration.

### Two-layer package structure

- `custom_components/waste_collection_schedule/` — Home Assistant integration layer (config flow, sensors, calendar, services).
- `custom_components/waste_collection_schedule/waste_collection_schedule/` — Core library (standalone, no HA dependency). Importable as `waste_collection_schedule`. Contains the data-fetching logic.

### Key components

- **Sources** (`waste_collection_schedule/source/`): ~600 provider-specific modules. Each is a single Python file exporting `TITLE`, `DESCRIPTION`, `URL`, `COUNTRY`, `TEST_CASES`, and a `Source` class with a `fetch()` method that returns `list[Collection]`.
- **Services** (`waste_collection_schedule/service/`): ~17 shared service modules used by multiple sources (e.g. `ICS`, `AbfallIO`, `AppAbfallplusDe`).
- **SourceShell** (`source_shell.py`): wraps source modules; handles customisation (aliases, icons, filtering) and the fetch lifecycle.
- **Wizard** (`waste_collection_schedule/wizard/`): multi-step config flow helpers for sources with cascading API lookups.
- **Config flow** (`config_flow.py`): UI-based setup using HA's config entries. Dynamically loads source modules and their parameters.

### Collection data model

`Collection(date, t, icon=None, picture=None)` — a single collection event with a date and waste-type string `t`.

---

## Build and test

```bash
# Automated test suite (pytest)
python -m pytest tests/

# Single test file
python -m pytest tests/test_source_components.py

# Specific test by name
python -m pytest tests/test_source_components.py -k "test_name"

# Test one source manually against its TEST_CASES
cd custom_components/waste_collection_schedule/waste_collection_schedule/test
python test_sources.py -s <source_name> -l

# All pre-commit hooks (ruff lint + format, mypy, codespell, bandit, pyupgrade, yamlfmt)
pre-commit run --all-files

# Install dependencies
pip install -r requirements.txt
```

`tests/test_source_components.py` validates structure (TITLE, URL, COUNTRY, TEST_CASES, EXTRA_INFO format, etc.) — it runs in CI for every PR. `waste_collection_schedule/test/test_sources.py` is a CLI tool for live-testing a source against its TEST_CASES; it is excluded from pytest.

---

## Linting and formatting

- **ruff** (replaces black, flake8 and isort): line-length 88, lint select `E,F,W,I` (pycodestyle + pyflakes + isort, profile=black), ignore `E203,E501,E721`. `ruff format` mirrors black; `ruff check` mirrors flake8 + isort. Config lives in `.pre-commit-config.yaml` / `pyproject.toml`.
- **mypy**: `--ignore-missing-imports --explicit-package-bases`
- **bandit**: config at `tests/bandit.yaml`
- **pyupgrade**: targets Python 3.7+
- **yamlfmt**: mapping=2, sequence=4, width=150, offset=2

For a single source file edit:

```bash
ruff check --fix <file>
ruff format <file>
```

---

## Source module contract

There are two source styles. The full guide is `doc/contributing_source.md`.

1. **`BaseSource` pipeline (preferred for new sources).** The source declares which reusable steps to use: `retrieve` (raw fetch) then `parse` (structure) then `preprocess` (records) then `transform` (one `Collection` per record). Metadata, `PARAMS` and the steps are class attributes; usually there is no source-specific code at all. No `__init__` (`BaseSource.__init__` takes the `PARAMS` fields as kwargs, applies their defaults, validates, and stores them on `self.params`), no `fetch()`, no per-source `ICON_MAP`, no manual date parsing. Use `classify()` instead of a transformer for irregular providers. See the converted examples (`kwinana_wa_gov_au.py`, `koppl_at.py`, `reading_gov_uk.py`).
2. **Legacy module-level contract (still fully supported).** Module-level `TITLE`/`URL`/... plus a `Source` class with a hand-written `fetch() -> list[Collection]` returning `Collection(date, t, icon=...)`. Around 600 sources use this. A bug fix to one does not need converting.

Both styles need this metadata (on the class for pipeline sources, at module level for legacy):

| Symbol | Type | Notes |
|---|---|---|
| `TITLE` | `str` | Display name. |
| `DESCRIPTION` | `str` | One-line description. |
| `URL` | `str` | Provider's website. |
| `COUNTRY` | `str` | **Lowercase code** from `update_docu_links.py`'s `COUNTRYCODES` list. UK = `"uk"` (NOT `"gb"`); Canada = `"ca"` (lowercase). An invalid value silently orphans the source out of README/info/sources.json. |
| `TEST_CASES` | `dict` | Maps test-case name to constructor kwargs. Must not be empty. |

Pipeline sources also declare `PARAMS` (typed `config_params` descriptors), `WASTE_TYPES`, the step attributes, and a `transformer` (or `classify()`), but no `__init__`. Legacy sources provide the `Source` class with `__init__(**kwargs)` and `fetch()`.

**Declare `WASTE_TYPES` explicitly**, as the canonical types the source actually produces, derived by replaying its cassette. `BaseSource.__init_subclass__` will auto-derive it, but only from a transformer's explicit `type_value_map`, so it misses everything the shared vocabulary resolves; a bare transformer with no map falls back to the whole `ALL_TYPES` catalogue, which declares nothing. `tests/test_declared_waste_types.py` replays every cassette and rejects both shapes. The list feeds the config-flow waste-type dropdown and nothing else.

**Pipeline membership is `issubclass(Source, BaseSource)`, never `PARAMS` truthiness.** A zero-parameter pipeline source declares `PARAMS = ()`, which is falsy; testing that instead hid 21 of the 266 pipeline sources from the whole v3 gate suite. Write the base-class check in any new tool or gate.

**Cassette rule (enforced).** Every pipeline source ships a recorded cassette under `tests/fixtures/<module>/`, **one per `TEST_CASES` entry**, named by slugging the case key (`"Amagerbrogade 10"` → `amagerbrogade_10.json`). CI replays them offline instead of calling live providers. Record with `python tests/record_fixtures.py <module>` and commit the JSON.

`TEST_CASES` and the cassettes are two halves of one test: the case declares the *inputs*, the cassette holds the *recorded provider responses* for those inputs, and the slug is the only link between them. Four gates in `tests/test_new_architecture.py` keep them in step:

| gate | what it catches |
|---|---|
| `test_pipeline_sources_ship_a_cassette` | a source with no recording at all (backlog: `SOURCES_AWAITING_CASSETTE`) |
| `test_every_test_case_ships_a_cassette` | a *case* with no recording, in a source that has others (backlog: `CASES_AWAITING_CASSETTE`) |
| `test_the_cassette_backlog_is_not_stale` / `..._source_cassette_backlog_is_not_stale` | a backlog entry that has since been recorded |
| `test_no_cassettes_without_a_source` | recordings left behind by a deleted source |

Both backlogs are debt registers, not exemptions: record the case and delete its line. Note an *empty* fixture directory is untracked local debris (git cannot store an empty directory) and does not count as a recording, which is what let the per-source backlog go stale. A shared-service source keeps one cassette per distinct response shape.

**What a cassette pins.** A recording stores the request body (every payload slot at once: `json`, `data`, `params`, `files`, canonically rendered), and replay fails if a source sends something the recording did not. Cassettes recorded before #7102 have no `body` field and are still matched on method and URL alone, pinning nothing about the payload; that is deliberate, because several sources cannot be re-recorded from outside their region. `FALLBACK_BUDGET` in `tests/test_offline_fixtures.py` counts how many requests are still matched that loosely and only ratchets down, so lower it whenever you re-record a source. `python -m pytest tests/test_offline_fixtures.py -k <module> -p tests.mutate_requests` alters every outgoing request and says which case a source is in: a replay that still passes checked nothing about what it sent.

**Reuse rule (enforced).** A pipeline source composes shared components; it does not define its own. Provider behaviour belongs in a reusable component under `waste_collection_schedule/service/` (or the shared retrievers/parsers modules), so the next provider on that platform gets it for free. This applies to conversions as much as to new sources: when porting a fix out of a legacy source, decide which layer the behaviour belongs to rather than copying it into the source module.

Two gates in `tests/test_new_architecture.py` enforce it, because the rule is about where behaviour lives, not how it is spelled:

| gate | what it catches | backlog |
|---|---|---|
| `test_pipeline_sources_reuse_shared_components` | a `Retriever`/`Parser` **subclass** declared in the source module | `SOURCE_LOCAL_STEP_EXCEPTIONS` (narrow allowlist) |
| `test_pipeline_sources_do_not_hand_roll_retrieval` | a module-level **function** in the source module that issues the provider's HTTP, however it reaches a component (`YearlyRetriever(prepare=...)`, `LookupChainRetriever(steps=...)`, …) | `SOURCES_HAND_ROLLING_RETRIEVAL` (debt register, staleness-checked) |

The second gate exists because the first read as comprehensive while missing a whole form of the thing it checks (#7139). `frankenberg_de` and `zva_sek_de` run one vendor module, both hand-rolled its dropdown decoder as plain functions, and the two copies drifted into four readings of one reply format with two bugs between them (#7100). Declaring retrieval with `def` rather than `class` does not make it reusable. When writing a gate, match on the property you care about, not on a proxy that usually correlates with it.

Optional:

- `REGIONS` (pipeline, preferred): a `list[Region]` (from `regions.region(title, **params)`) declaring the regions one structure covers, each becoming its own discoverable listing in the README / `sources.json` with its `params` pre-filled. A source is one structure (pipeline + `PARAMS`) applied to one or more regions; a single-region source leaves it empty. For a platform covering dozens of providers, the registry is data: put it in `doc/regions/<source>.yaml` and declare `REGIONS = regions.from_yaml("<source>", <param>="<key>")`, so adding a provider is a change to one data file. `test_pipeline_sources_keep_registries_as_data` enforces that. Build-time only, because `doc/` is not shipped in a HACS install, which is fine for `REGIONS` (the config flow reads the generated JSON) but means a registry the source needs while fetching must stay in Python.
- `EXTRA_INFO` (**legacy sources only**): the older dict form (`title`, `url`, `country`, `default_params`) of the same idea, read from module level on legacy sources. **A pipeline source must not declare it**, because its params are not validated against `PARAMS`, and `test_pipeline_sources_do_not_use_extra_info` rejects one that does. `regions.from_extra_info()` adapts it into `Region`s at one boundary so the rest of the toolchain works in `Region` terms only, and that adapter is deleted with the last legacy source (`doc/legacy_deprecation_plan.md`).
- `RAISE_ON_EMPTY` (pipeline): set `True` on address/lookup sources so an empty result raises instead of returning `[]`.
- `HOWTO` (pipeline) / `HOW_TO_GET_ARGUMENTS_DESCRIPTION` (legacy): per-language guidance shown in the config form.
- `PARAM_TRANSLATIONS` / `PARAM_DESCRIPTIONS` / `HOW_TO_GET_ARGUMENTS_DESCRIPTION` (**legacy sources only**): per-language argument labels and descriptions, read by `update_docu_links.py`. A legacy source needs them because it has no `PARAMS` to hang labels on. **A pipeline source must not declare one**, and `test_pipeline_sources_do_not_use_legacy_translations` rejects it: labels and help come from `field_terms.py` via `PARAMS`, in all five languages at once, and `HOWTO` covers per-language guidance.
- `SOURCE_CODEOWNERS` (one name for both styles: a pipeline class attribute or a legacy module variable): `list[str]` of GitHub handles (e.g. `["@your-handle"]`), each starting with `@`. `update_docu_links.py` writes these into `.github/source_owners.json`; a GitHub Action pings and assigns the listed owners when a bug report names this source. **Strongly encouraged for all new sources.** ICS YAML providers use the equivalent `codeowners:` key in their `.yaml` file.

### CI-enforced structural rules

`tests/test_source_components.py` runs in CI on every PR and enforces:

1. **Language allowlist:** `PARAM_TRANSLATIONS` and `PARAM_DESCRIPTIONS` keys MUST be in `{"en", "de", "it", "fr", "nl"}` (the `LANGUAGES` list in `update_docu_links.py` is the source of truth). **Default behaviour when a contributor / agent wants to use any other language** (e.g. `fi`, `es`, `pl`): strip the unsupported-language block from the source's translation dicts in the current PR, and open a *separate* issue titled `Add <lang> (xx) language support to PARAM_TRANSLATIONS allowlist` linked back to the original PR/issue, asking for contributors to help with the full translation pipeline (allowlist + `update_docu_links.py` + `translations/<xx>.json`). Never silently include an unsupported language; CI will reject the PR.
2. **Icons enum (legacy sources):** `ICON_MAP` values MUST be members of the `Icons` enum (`from waste_collection_schedule import Icons`). Raw `"mdi:..."` strings fail the `test_icon_map_uses_canonical_icons` check. The canonical catalogue is at `custom_components/waste_collection_schedule/waste_collection_schedule/icons.py`; pick the nearest sensible member and do not extend the enum in a source PR. Pipeline sources have no `ICON_MAP`: the icon comes from the canonical `WasteType` the transformer resolves, so this rule does not apply to them.
3. **COUNTRY allowlist** as already noted above.

Run `python -m pytest tests/test_source_components.py -q` locally after any source-module change and before committing; do not rely on CI to catch these.

### Exception handling

Use `SourceArgumentNotFound` / `SourceArgumentNotFoundWithSuggestions` from `waste_collection_schedule.exceptions`, not generic `Exception`. The HA UI surfaces these to the user with helpful context.

### Cloudflare-protected sites

Always try `curl_cffi` first:

```python
from curl_cffi import requests
session = requests.Session(impersonate="chrome")
```

If a site returns 403 with regular `requests`, switch to `curl_cffi` — it bypasses Cloudflare in most cases. See `east_renfrewshire_gov_uk.py` and `south_ayrshire_gov_uk.py` for examples.

### What NOT to do

- ❌ Hardcoded dates or schedules. Sources must fetch from a live API, ICS feed, or webpage.
- ❌ `if __name__ == "__main__":` blocks or standalone-script boilerplate.
- ❌ Dummy parameters (e.g. `_`) just to satisfy the config GUI.
- ❌ Login-required sources. The project only supports publicly accessible endpoints.
- ❌ Sources for providers already covered by a shared platform: check `recollect.yaml`, `mein_abfallkalender_online.yaml`, `recyclecoach_com.py`'s `EXTRA_INFO` list, `c_trace_de`, `service/OpenCities.py` (OpenCities/MyArea council CMS widget: `api/v1/myarea/search` + `ocapi/Public/myarea/wasteservices` endpoints), and the other shared platforms first. This now includes the componentised pipeline platforms in `waste_collection_schedule/service/`: ArcGIS, RiSKommunal (AT), AchieveForms / FirmstepSelfService (UK), IntraMaps, Abfallnavi / regio iT (DE), Sitepark IES (DE), Pozi (AU), WhatBinDay (AU), Sepan (PL), Junker app (IT), A Region (CH), Ecoharmonogram (PL), Cloud9 apps (UK), and the whole ICS platform (the generic `ics` source plus the `doc/ics/yaml/*.yaml` providers it folds in). See `doc/contributing_source.md`'s "Reusable service platforms" table for the full, current list.

---

## Generated files — never edit these manually

These files are produced by `update_docu_links.py`, which runs automatically via the `Update Documentation` CI workflow on every push to `master` (post-merge). **Never run `update_docu_links.py` yourself in a PR branch, and never commit changes to these files:**

- `README.md`, `info.md`
- `custom_components/waste_collection_schedule/sources.json`
- `custom_components/waste_collection_schedule/source_metadata.json`
- `custom_components/waste_collection_schedule/translations/{en,de,it,fr,nl}.json` (config-flow `args_*` sections only; the `options.step.init` section IS hand-maintained)
- `custom_components/waste_collection_schedule/waste_collection_schedule/translations/*.json`
- `doc/ics/*.md` (one per `doc/ics/yaml/*.yaml`)

If a PR diff touches any of the above, revert with `git checkout upstream/master -- <file>` before pushing.

### Files that ARE editable

- `custom_components/waste_collection_schedule/waste_collection_schedule/source/*.py` (source modules).
- `doc/source/<id>.md`: for **legacy** sources, **must be created manually** (the update script reads but does not create these). For **pipeline** (`BaseSource`) sources, `doc_generator.py` renders this from the class metadata during the post-merge generation run, so do not hand-write it.
- `doc/source/ics.md`, `doc/source/static.md` — manually maintained (blacklisted from generation, except for an auto-patched service-table section in each).
- `doc/ics/yaml/*.yaml`: ICS provider definitions. Each file generates the matching `doc/ics/<name>.md`. One definition may cover several providers: list the others under `regions:` (each becomes its own README / `sources.json` listing, via `ics.REGIONS`). This key was called `extra_info:` until 2026-08, which confusingly named it after the deprecated Python `EXTRA_INFO` attribute it has nothing to do with; `ics.py` still reads the old spelling, but write `regions:`.
  Some providers also list their per-provider **service endpoints** inside `howto`, which is a different thing from the `regions:` URL and is not generated from it: `regions[].url` is the provider's own website (for the listing), while the howto list gives the URL the user pastes as the `url` parameter. Both need maintaining where both apply.
- `CHANGELOG.md`, `manifest.json` — manually maintained (release-time only).

---

## Common pitfalls (read before implementing or reviewing a source)

These are the issues that come up most often in PR review. Avoid them and your PR will sail through.

1. **`COUNTRY` mismatch**. Must be a lowercase code from `update_docu_links.py`'s `COUNTRYCODES` list. UK = `"uk"`, Canada = `"ca"`. An invalid value silently orphans the source — CI did not catch this in the past.
2. **Generated files in the diff**. See list above. Revert before pushing.
3. **Missing `doc/source/<id>.md`** (legacy sources). Required for every new legacy source; create it manually. Pipeline (`BaseSource`) sources have it auto-generated, so do not hand-write one.
4. **Hardcoded data**. Fetch live; do not paste a schedule.
5. **Provider already covered by a shared platform** (Recollect, RecycleCoach, ICS YAML, Publidata, IntraMaps, OpenCities/MyArea, etc.). Check first.
6. **Generic `Exception`**. Use `SourceArgumentNotFound` / `SourceArgumentNotFoundWithSuggestions`.
7. **403 from a Cloudflare site**. Switch to `curl_cffi`.
8. **Login-required**. Not supported — the project only consumes public endpoints.
9. **Running `update_docu_links.py` in a PR branch**. Don't — CI handles it post-merge.
10. **Editing translations directly**. The `config.step.args_*` sections are generated. Hand-edit only `options.step.init` (in the outer `translations/*.json`).
11. **Raw `mdi:*` strings in `ICON_MAP`** (legacy sources). Use the `Icons` enum from `waste_collection_schedule` (catalogue at `waste_collection_schedule/icons.py`). This keeps icons consistent across sources for the same logical waste category (see #2813). Pipeline sources have no `ICON_MAP`: the icon comes from the canonical `WasteType`.

---

## Contributor workflow

If you're a contributor: see `.claude/commands/new-source.md` or run `/new-source`. The agents under `.claude/agents/source-*` walk you through investigating a provider, implementing the source, and submitting a PR.

Branch and PR target: **always** open PRs against `mampfes/hacs_waste_collection_schedule:master` from a feature branch on your fork. Never push to your fork's `master`.

## Maintainer workflow

If you're a maintainer: see `.claude/commands/{review-pr,review-issue,cleanup}.md`. Each spawns a planner agent that produces a Phase 1 report; on approval, an executor agent runs the plan in an isolated worktree.

Key workflow rules:

- **Always present drafts before posting on GitHub.** Reviews, comments, label changes, closes — show the user the exact text first.
- **Fix minor issues yourself; escalate substantive ones.** Style, whitespace, missing doc file, lint failures → push the fix to the contributor's branch and approve. Hardcoded data, missing API integration, security issues → request changes.
- **Never commit directly to `master`** — local, origin, or upstream. Every change goes through a feature branch and PR to upstream.
- **Never run `update_docu_links.py` manually.** CI runs it post-merge.
- **After merge, clean up.** `/cleanup` syncs `master` with upstream, deletes merged branches locally and on origin, removes any contributor fork remotes.
- **Never ask users for their address or identifying information.** Use existing TEST_CASES or ask for known-good public examples.

### Versioning and deprecation

The project follows **strict semantic versioning** (Option A, agreed in [discussion #6622](https://github.com/mampfes/hacs_waste_collection_schedule/discussions/6622)). Full policy: `doc/versioning.md`.

- **Bump = highest-severity change.** Patch: fixes, deps, docs/infra. Minor: additions (new sources, platforms, params, countries) and new deprecations. Major: breaking changes (removals, config-schema or entity-ID changes, waste-type label changes, dropping an HA version).
- **A pipeline source migration is breaking (major),** because it changes waste-type labels; migrations are batched behind one major, shipped first as an `X.0.0-alpha`/`beta`. The legacy `fetch()` contract stays supported as the per-source rollback path.
- **Deprecation lifecycle:** keep a compat shim only when removal would change entity IDs; announce via a one-time runtime warning, a CHANGELOG `Deprecated` entry, and a `DEPRECATIONS.md` row; keep for at least two minor releases; batch removals into the next major.

---

## Project resources

- Upstream: https://github.com/mampfes/hacs_waste_collection_schedule
- HACS integration: install via HACS by adding this repository as a custom repository
- Contributor docs: `CONTRIBUTING.md`
