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

# All pre-commit hooks (black, flake8, isort, mypy, codespell, bandit, pyupgrade, yamlfmt)
pre-commit run --all-files

# Install dependencies
pip install -r requirements.txt
```

`tests/test_source_components.py` validates structure (TITLE, URL, COUNTRY, TEST_CASES, EXTRA_INFO format, etc.) — it runs in CI for every PR. `waste_collection_schedule/test/test_sources.py` is a CLI tool for live-testing a source against its TEST_CASES; it is excluded from pytest.

---

## Linting and formatting

- **black**: `--safe --quiet`
- **flake8** ignores: D100–D107, E501, W503, E203
- **isort**: profile=black, multi-line=3, trailing-comma
- **mypy**: `--ignore-missing-imports --explicit-package-bases`
- **bandit**: config at `tests/bandit.yaml`
- **pyupgrade**: targets Python 3.7+
- **yamlfmt**: mapping=2, sequence=4, width=150, offset=2

For a single source file edit:

```bash
python -m black <file>
python -m isort --profile black <file>
```

---

## Source module contract

Every source file in `custom_components/waste_collection_schedule/waste_collection_schedule/source/` must define:

| Symbol | Type | Notes |
|---|---|---|
| `TITLE` | `str` | Display name. |
| `DESCRIPTION` | `str` | One-line description. |
| `URL` | `str` | Provider's website. |
| `COUNTRY` | `str` | **Lowercase code** from `update_docu_links.py`'s `COUNTRYCODES` list. UK = `"uk"` (NOT `"gb"`); Canada = `"ca"` (lowercase). An invalid value silently orphans the source out of README/info/sources.json. |
| `TEST_CASES` | `dict` | Maps test-case name → constructor kwargs. Must not be empty. |
| `Source` class | | `__init__(**kwargs)` and `fetch() -> list[Collection]`. |

Optional:

- `EXTRA_INFO` — list of dicts (`title`, `url`, `country`, `default_params`) for sources that cover multiple municipalities under one module.
- `TITLE_LANG` / `EXTRA_INFO_LANG` — non-English titles.
- `HOW_TO_GET_ARGUMENTS_DESCRIPTION` — per-language guidance shown in the config wizard.
- `PARAM_TRANSLATIONS` / `PARAM_DESCRIPTIONS` — per-language argument labels and descriptions. Currently still required on master (read by `update_docu_links.py` to generate `translations/en.json`). A future i18n YAML migration will replace these but is not yet merged — keep them.

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
- ❌ Sources for providers already covered by a shared platform — check `recollect.yaml`, `mein_abfallkalender_online.yaml`, `recyclecoach_com.py`'s `EXTRA_INFO` list, `c_trace_de`, and the other shared platforms first.

---

## Generated files — never edit these manually

These files are produced by `update_docu_links.py`, which runs automatically via the `Update Documentation` CI workflow on every push to `master` (post-merge). **Never run `update_docu_links.py` yourself in a PR branch, and never commit changes to these files:**

- `README.md`, `info.md`
- `custom_components/waste_collection_schedule/sources.json`
- `custom_components/waste_collection_schedule/source_metadata.json`
- `custom_components/waste_collection_schedule/translations/{en,de,it,fr}.json` (config-flow `args_*` sections only — the `options.step.init` section IS hand-maintained)
- `custom_components/waste_collection_schedule/waste_collection_schedule/translations/*.json`
- `doc/ics/*.md` (one per `doc/ics/yaml/*.yaml`)

If a PR diff touches any of the above, revert with `git checkout upstream/master -- <file>` before pushing.

### Files that ARE editable

- `custom_components/waste_collection_schedule/waste_collection_schedule/source/*.py` — source modules.
- `doc/source/<id>.md` — **must be created manually** for each new source. The update script reads but does not create these.
- `doc/source/ics.md`, `doc/source/static.md` — manually maintained (blacklisted from generation, except for an auto-patched service-table section in each).
- `doc/ics/yaml/*.yaml` — ICS provider definitions. Each file generates the matching `doc/ics/<name>.md`. When adding a provider, update BOTH the `extra_info` list (for the README/sources.json listing) AND the table inside the `howto.en` string (for the generated `.md`).
- `CHANGELOG.md`, `manifest.json` — manually maintained (release-time only).

---

## Common pitfalls (read before implementing or reviewing a source)

These are the issues that come up most often in PR review. Avoid them and your PR will sail through.

1. **`COUNTRY` mismatch**. Must be a lowercase code from `update_docu_links.py`'s `COUNTRYCODES` list. UK = `"uk"`, Canada = `"ca"`. An invalid value silently orphans the source — CI did not catch this in the past.
2. **Generated files in the diff**. See list above. Revert before pushing.
3. **Missing `doc/source/<id>.md`**. Required for every new source; create it manually.
4. **Hardcoded data**. Fetch live; do not paste a schedule.
5. **Provider already covered by a shared platform** (Recollect, RecycleCoach, ICS YAML, Publidata, IntraMaps, etc.). Check first.
6. **Generic `Exception`**. Use `SourceArgumentNotFound` / `SourceArgumentNotFoundWithSuggestions`.
7. **403 from a Cloudflare site**. Switch to `curl_cffi`.
8. **Login-required**. Not supported — the project only consumes public endpoints.
9. **Running `update_docu_links.py` in a PR branch**. Don't — CI handles it post-merge.
10. **Editing translations directly**. The `config.step.args_*` sections are generated. Hand-edit only `options.step.init` (in the outer `translations/*.json`).

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

---

## Project resources

- Upstream: https://github.com/mampfes/hacs_waste_collection_schedule
- HACS integration: install via HACS by adding this repository as a custom repository
- Contributor docs: `CONTRIBUTING.md`
