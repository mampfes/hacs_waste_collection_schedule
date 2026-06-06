---
description: Implement a new source from a vetted investigation report, including docs and validation.
---

You are the `source-implementer` agent equivalent for GitHub Copilot.

Input requirement: use a prior investigation report. If missing, ask for it first.

When implementing a new Python source:
- Create `custom_components/waste_collection_schedule/waste_collection_schedule/source/<module>.py`.
- Create `doc/source/<module>.md`.

When implementing ICS provider support:
- Create `doc/ics/yaml/<provider>.yaml` (do not create generated `doc/ics/<provider>.md`).

Rules:
- Define TITLE, DESCRIPTION, URL, COUNTRY, TEST_CASES, Source class.
- Keep COUNTRY as lowercase code from `COUNTRYCODES`.
- Use `SourceArgumentNotFound`/`SourceArgumentNotFoundWithSuggestions` for input errors.
- No hardcoded schedules, no `if __name__ == "__main__"` blocks, no dummy parameters.
- Use `Icons` enum for ICON_MAP values (no raw `mdi:*` strings).
- Do not manually run `update_docu_links.py`.
- Do not modify generated files (`README.md`, `info.md`, `sources.json`, `source_metadata.json`, `translations/*.json`, `doc/ics/*.md`).

Validation:
- Format changed Python files with black + isort.
- Run `python -m pytest tests/test_source_components.py -q`.
- Run `python test_sources.py -s <module> -l` from the test directory when applicable.

Return an Implementation Report with changed files, test results, open questions, and next steps.
