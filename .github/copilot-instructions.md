# GitHub Copilot instructions

These are project-specific instructions for GitHub Copilot when assisting contributors. The full set of contributor guidance lives in [`AGENTS.md`](../AGENTS.md) at the repo root — that file applies equally here.

For the human-facing guide, see [`doc/contributing.md`](../doc/contributing.md).

## Quick reference

**Project layout:** Two nested packages. The HA integration layer is `custom_components/waste_collection_schedule/`. The core library is the inner `custom_components/waste_collection_schedule/waste_collection_schedule/` (importable as `waste_collection_schedule`). Source modules live at `.../source/<provider>.py`.

**Source contract:** Every source file defines `TITLE`, `DESCRIPTION`, `URL`, `TEST_CASES`, and a `Source` class with `fetch() -> list[Collection]`. Use `Collection(date, t, icon=None, picture=None)` as the data model.

**Don't hand-edit generated files.** `README.md`, `info.md`, `sources.json`, `source_metadata.json`, `translations/{en,de,it,fr}.json`, and `doc/ics/*.md` are all produced by `update_docu_links.py` from the source modules and `doc/ics/yaml/*.yaml`. Edit the sources and re-run the script.

**ICS feeds:** Prefer adding a YAML at `doc/ics/yaml/<name>.yaml` over a new source file. The generic `ics` source consumes it. Use `{%Y}` for a year placeholder.

## Things reviewers consistently reject

- Hardcoded dates or weekday rules — sources must fetch from a real upstream (API, ICS, or scrapeable HTML).
- Generic `Exception` — use `SourceArgumentNotFound` / `SourceArgumentNotFoundWithSuggestions` for invalid user input.
- `if __name__ == "__main__"` blocks in source modules.
- Dummy parameters added just to satisfy the config GUI.
- Missing `update_docu_links.py` run (CI fails on stale generated files).
- Silent `[]` returns on HTTP errors (masks failures as "no upcoming collections").

## Useful commands

```bash
python -m pytest tests/                                        # run automated test suite
python custom_components/.../test/test_sources.py -s <name> -l  # test one source
python -m black <path> && python -m isort --profile black <path>
python -m flake8 --extend-ignore=D100,D101,D102,D103,D104,D105,D106,D107,E501,W503,E203 <path>
python update_docu_links.py                                    # regenerate docs/metadata
```

PRs target `master` of `mampfes/hacs_waste_collection_schedule`.
