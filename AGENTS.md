# Contributor instructions for AI coding assistants

This file is written for AI coding assistants (Claude Code, Cursor, codex, Aider, etc.) helping contributors add or fix sources in this repository. GitHub Copilot reads `.github/copilot-instructions.md` instead — that file mirrors this one.

For the full human-facing guide, see [`doc/contributing.md`](doc/contributing.md).

## Project layout

Two nested packages:

- `custom_components/waste_collection_schedule/` — Home Assistant integration layer (config flow, sensors, calendar, services).
- `custom_components/waste_collection_schedule/waste_collection_schedule/` — Core library, importable as `waste_collection_schedule`. No HA dependency.

Source modules live at `custom_components/waste_collection_schedule/waste_collection_schedule/source/<provider>.py`. Shared platforms (used by multiple sources) live at `.../service/<Platform>.py`.

## Source module contract

Every file under `source/` must define:

- `TITLE: str` — display name shown in the README and config flow.
- `DESCRIPTION: str` — one-line summary.
- `URL: str` — provider website.
- `TEST_CASES: dict[str, dict]` — at least one working test case (constructor kwargs).
- A `Source` class with `__init__(**kwargs)` and `fetch() -> list[Collection]`.

Optional but recommended:

- `COUNTRY: str` (ISO-3166-1 alpha-2, lower-case).
- `EXTRA_INFO: list[dict]` for sources that cover multiple municipalities.
- `PARAM_DESCRIPTIONS`, `PARAM_TRANSLATIONS`, `HOW_TO_GET_ARGUMENTS_DESCRIPTION` keyed by language code. **Only `en`, `de`, `it`, `fr` are supported** — other codes (e.g. `lt`, `pl`, `nl`) will fail the test suite.

`Collection(date, t, icon=None, picture=None)` is the data model. Return one per collection event.

## Files you must NOT hand-edit

The following are regenerated automatically by CI after every merge to `master`. **Do not edit them in your PR branch** — your changes will be overwritten:

- `README.md`, `info.md`
- `custom_components/waste_collection_schedule/sources.json`
- `custom_components/waste_collection_schedule/source_metadata.json`
- `custom_components/waste_collection_schedule/translations/{en,de,it,fr}.json`
- `doc/ics/*.md` (generated from `doc/ics/yaml/*.yaml`)

`doc/source/*.md` is **not** generated — you must create one manually for each new source.

## ICS providers

If the provider exposes an ICS feed, prefer adding a single YAML at `doc/ics/yaml/<name>.yaml` over writing a new source file. The generic `ics` source consumes it. Use `{%Y}` as a year placeholder if the URL embeds the current year. CI will regenerate the corresponding `doc/ics/<name>.md` automatically after merge — do not run `update_docu_links.py` in your PR branch.

## Common review rejections

Things the maintainers consistently bounce in code review — avoid these from the start:

- **Hardcoded dates or weekday rules.** Sources must fetch from a real, dated upstream (API, ICS, or scrapeable HTML). A rule like "Recycling is every other Monday" is not acceptable.
- **Generic `Exception`.** Use `SourceArgumentNotFound` or `SourceArgumentNotFoundWithSuggestions` from `waste_collection_schedule.exceptions` for missing/invalid user input. Bubble up `requests.HTTPError` for upstream failures.
- **`if __name__ == "__main__"` blocks.** Sources are libraries; no standalone entry points.
- **Dummy parameters** added solely to satisfy the config GUI. If a parameter has no use, drop it.
- **Unsupported language codes in `PARAM_DESCRIPTIONS` / `PARAM_TRANSLATIONS`.** Only `en`, `de`, `it`, `fr` are valid keys. Including any other code (e.g. `lt`, `nl`, `pl`) fails `test_source_has_necessary_parameters`.
- **Editing files in the "must not hand-edit" list above** — they get overwritten by CI after merge.
- **Suppressing failures silently.** Returning `[]` on an HTTP error masks problems as "no upcoming collections".
- **Unformatted code.** Run `black` and `isort` before committing (see Commands below).

## Commands

```bash
# Run the full automated test suite
python -m pytest tests/

# Test a specific source against its TEST_CASES
cd custom_components/waste_collection_schedule/waste_collection_schedule/test
python test_sources.py -s <source_name> -l

# Format before every commit — REQUIRED on every file you change
python -m black <path>
python -m isort --profile black <path>

# Lint
python -m flake8 --extend-ignore=D100,D101,D102,D103,D104,D105,D106,D107,E501,W503,E203 <path>

# Activate the git pre-commit hook (run once after cloning — enforces formatting automatically)
pre-commit install
```

`pre-commit run --all-files` runs the full lint suite (black, flake8, isort, mypy, codespell, bandit, pyupgrade, yamlfmt).

> **AI agents:** Always run `python -m black <path> && python -m isort --profile black <path>` on every changed file before calling `git commit`. The pre-commit hook enforces this for human contributors; agents must do it explicitly.

> **Note:** Do not run `update_docu_links.py` in a PR branch. The `Update Documentation` CI workflow runs it automatically on every push to `master` (post-merge) and commits the generated output.

## Example sources to model on

- HTML scraping (BeautifulSoup): [`source/birmingham_gov_uk.py`](custom_components/waste_collection_schedule/waste_collection_schedule/source/birmingham_gov_uk.py)
- ICS-based: [`source/stadtreinigung_hamburg.py`](custom_components/waste_collection_schedule/waste_collection_schedule/source/stadtreinigung_hamburg.py)
- JSON/REST API: [`source/toronto_ca.py`](custom_components/waste_collection_schedule/waste_collection_schedule/source/toronto_ca.py)

## Pull request checklist

1. Source module passes `test_sources.py -s <name>` against real TEST_CASES.
2. New `doc/source/<name>.md` exists.
3. `python -m pytest tests/` passes locally.
4. Changed files are formatted with `black` and `isort --profile black`.
5. PR targets `master` of `mampfes/hacs_waste_collection_schedule`.
6. Do **not** commit changes to `README.md`, `info.md`, `sources.json`, `source_metadata.json`, `translations/*.json`, or `doc/ics/*.md` — CI regenerates these after merge.
