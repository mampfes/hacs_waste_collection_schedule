# GitHub Copilot instructions

These are project-specific instructions for GitHub Copilot when assisting contributors. The full set of contributor guidance lives in [`AGENTS.md`](../AGENTS.md) at the repo root — that file applies equally here.

For the human-facing guide, see [`doc/contributing.md`](../doc/contributing.md).

## Quick reference

**Project layout:** Two nested packages. The HA integration layer is `custom_components/waste_collection_schedule/`. The core library is the inner `custom_components/waste_collection_schedule/waste_collection_schedule/` (importable as `waste_collection_schedule`). Source modules live at `.../source/<provider>.py`.

**Source contract:** Every source file defines `TITLE`, `DESCRIPTION`, `URL`, `TEST_CASES`, and a `Source` class with `fetch() -> list[Collection]`. Use `Collection(date, t, icon=None, picture=None)` as the data model.

**Don't hand-edit generated files.** `README.md`, `info.md`, `sources.json`, `source_metadata.json`, `translations/{en,de,it,fr}.json`, and `doc/ics/*.md` are all produced by `update_docu_links.py`. CI regenerates them automatically after every merge to `master` — do not run the script in your PR branch, and do not commit changes to these files.

**ICS feeds:** Prefer adding a YAML at `doc/ics/yaml/<name>.yaml` over a new source file. The generic `ics` source consumes it. Use `{%Y}` for a year placeholder. CI regenerates `doc/ics/<name>.md` after merge — do not run `update_docu_links.py` in your PR branch.

## Things reviewers consistently reject

- Hardcoded dates or weekday rules — sources must fetch from a real upstream (API, ICS, or scrapeable HTML).
- Generic `Exception` — use `SourceArgumentNotFound` / `SourceArgumentNotFoundWithSuggestions` for invalid user input.
- `if __name__ == "__main__"` blocks in source modules.
- Dummy parameters added just to satisfy the config GUI.
- Unsupported language codes in `PARAM_DESCRIPTIONS` / `PARAM_TRANSLATIONS` — only `en`, `de`, `it`, `fr` are valid.
- Committing generated files (`README.md`, `sources.json`, etc.) — CI handles these post-merge.
- Silent `[]` returns on HTTP errors (masks failures as "no upcoming collections").
- Unformatted code — always run `python -m black <path> && python -m isort --profile black <path>` before committing.

## Useful commands

```bash
python -m pytest tests/                                          # run automated test suite
python custom_components/.../test/test_sources.py -s <name> -l  # test one source
python -m black <path> && python -m isort --profile black <path> # format before committing
python -m flake8 --extend-ignore=D100,D101,D102,D103,D104,D105,D106,D107,E501,W503,E203 <path>
pre-commit install                                               # activate git hook (run once after cloning)
```

PRs target `master` of `mampfes/hacs_waste_collection_schedule`.
