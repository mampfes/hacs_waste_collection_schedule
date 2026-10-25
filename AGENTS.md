# Contributor instructions for AI coding assistants

This file is written for AI coding assistants (Claude Code, Cursor, codex, Aider, etc.) helping contributors add or fix sources in this repository. GitHub Copilot reads `.github/copilot-instructions.md` instead — that file mirrors this one.

For the full human-facing guide, see [`CONTRIBUTING.md`](CONTRIBUTING.md).

> **Claude Code users:** Claude Code also reads [`CLAUDE.md`](CLAUDE.md) (a role-aware project guide) and exposes specialised slash commands. Use `/new-source` to be walked through investigating a provider, generating the source module, and submitting a PR. See [`.claude/agents/`](.claude/agents/) for the full list of available agents.

## Project layout

Two nested packages:

- `custom_components/waste_collection_schedule/` — Home Assistant integration layer (config flow, sensors, calendar, services).
- `custom_components/waste_collection_schedule/waste_collection_schedule/` — Core library, importable as `waste_collection_schedule`. No HA dependency.

Source modules live at `custom_components/waste_collection_schedule/waste_collection_schedule/source/<provider>.py`. Shared platforms (used by multiple sources) live at `.../service/<Platform>.py`.

## New sources: branch and architecture

New Python sources must target `release/3.0.0` of `mampfes/hacs_waste_collection_schedule`. Base the feature branch on `release/3.0.0`; changing only the PR target does not convert a legacy implementation. Bug fixes for the current stable release still target `master`, and fixes to existing legacy sources do not require migration.

New sources must use the `BaseSource` pipeline. New legacy-style sources with a hand-written `fetch()` are not accepted. Follow the [release branch contribution guide](https://github.com/mampfes/hacs_waste_collection_schedule/blob/release/3.0.0/doc/contributing_source.md), [source skeleton](https://github.com/mampfes/hacs_waste_collection_schedule/blob/release/3.0.0/doc/new_source_template.py), and [PR template](https://github.com/mampfes/hacs_waste_collection_schedule/blob/release/3.0.0/.github/PULL_REQUEST_TEMPLATE.md).

- Declare metadata and typed `PARAMS` on `Source(BaseSource)`; use canonical waste types rather than a per-source icon map.
- Compose shared retrievers, parsers, preprocessors, and transformers. Extend shared components under `service/` when needed rather than adding source-local retrieval/parsing steps or HTTP callbacks.
- Record real `TEST_CASES` with `python tests/record_fixtures.py <module>` and commit the resulting `tests/fixtures/<module>/*.json`. Explain any genuine recording blocker in the PR summary.
- Pipeline source documentation in `doc/source/` is generated from class metadata; do not hand-write or commit it.

The legacy-specific contracts, icon rules, language rules, and examples below apply to existing sources on `master`. For new sources, use the release branch guide above.

## Legacy source module contract (stable fixes)

Every legacy file under `source/` must define:

- `TITLE: str` — display name shown in the README and config flow.
- `DESCRIPTION: str` — one-line summary.
- `URL: str` — provider website.
- `TEST_CASES: dict[str, dict]` — at least one working test case (constructor kwargs).
- A `Source` class with `__init__(**kwargs)` and `fetch() -> list[Collection]`.

Optional but recommended:

- `COUNTRY: str` (ISO-3166-1 alpha-2, lower-case).
- `EXTRA_INFO: list[dict]` for sources that cover multiple municipalities.
- `PARAM_DESCRIPTIONS`, `PARAM_TRANSLATIONS`, `HOW_TO_GET_ARGUMENTS_DESCRIPTION` keyed by language code. **Only `en`, `de`, `it`, `fr` are supported** — other codes (e.g. `lt`, `pl`, `nl`) will fail `test_source_has_necessary_parameters`. See the [HOW_TO_GET_ARGUMENTS_DESCRIPTION rules](#how_to_get_arguments_description-rules) section below.

`Collection(date, t, icon=None, picture=None)` is the data model. Return one per collection event. For `icon`, use a member of the canonical `Icons` enum (`from waste_collection_schedule import Icons` — full catalogue at `custom_components/waste_collection_schedule/waste_collection_schedule/icons.py`) rather than a raw `"mdi:..."` string.

## Files you must NOT hand-edit

The following are regenerated automatically by CI after every merge to `master`. **Do not edit them in your PR branch** — your changes will be overwritten:

- `README.md`, `info.md`
- `custom_components/waste_collection_schedule/sources.json`
- `custom_components/waste_collection_schedule/source_metadata.json`
- `custom_components/waste_collection_schedule/translations/{en,de,it,fr}.json`
- `doc/ics/*.md` (generated from `doc/ics/yaml/*.yaml`)

`doc/source/*.md` is hand-maintained for legacy sources on `master`. For pipeline sources on `release/3.0.0`, it is generated from class metadata and must not be committed.

## Icons

The integration ships with a canonical icon catalogue (`Icons` enum at `custom_components/waste_collection_schedule/waste_collection_schedule/icons.py`). Use it for all `ICON_MAP` values:

```py
from waste_collection_schedule import Collection, Icons

ICON_MAP = {
    "Glass": Icons.GLASS,
    "Paper": Icons.PAPER,
}
```

**Adding a new catalogue member is gated.** Only propose a new `Icons.*` member when (a) your provider returns a category that doesn't fit any existing member, AND (b) the category is general enough to expect other sources to use it. Open an issue first — propose name + MDI icon + example providers — and wait for maintainer agreement. Then a small separate PR adds the member, after which your source PR can use it. Do not add raw `"mdi:..."` strings to `ICON_MAP` to skip this conversation.

**Personal taste is not a catalogue concern.** If a user just prefers a different MDI icon for a waste category, they override it locally via `customize.icon` in their YAML (or via the GUI's icon picker). No source change needed:

```yaml
waste_collection_schedule:
  sources:
    - name: my_source
      args: { ... }
      customize:
        - type: "Glass"
          icon: mdi:bottle-wine
```

See `doc/contributing_source.md` for the full version of these rules.

## ICS providers

If the provider exposes an ICS feed, prefer adding a single YAML at `doc/ics/yaml/<name>.yaml` over writing a new source file. The generic `ics` source consumes it. Use `{%Y}` as a year placeholder if the URL embeds the current year. CI will regenerate the corresponding `doc/ics/<name>.md` automatically after merge — do not run `update_docu_links.py` in your PR branch.

## Source ownership (encouraged for all new sources)

If you add a new Python source, consider declaring yourself as an owner by adding `SOURCE_CODEOWNERS` to the module:

```python
SOURCE_CODEOWNERS = ["@your-github-handle"]
```

For a new ICS YAML provider, add the `codeowners` key:

```yaml
codeowners:
  - "@your-github-handle"
```

Owners are automatically pinged and assigned when a bug report is filed for their source. This is the primary way maintainers know who to contact when a source breaks. Every handle must start with `@`.

## Common review rejections

Things the maintainers consistently bounce in code review — avoid these from the start:

- **Hardcoded dates or weekday rules.** Sources must fetch from a real, dated upstream (API, ICS, or scrapeable HTML). A rule like "Recycling is every other Monday" is not acceptable.
- **Generic `Exception`.** Use `SourceArgumentNotFound` or `SourceArgumentNotFoundWithSuggestions` from `waste_collection_schedule.exceptions` for missing/invalid user input. Bubble up `requests.HTTPError` for upstream failures.
- **`if __name__ == "__main__"` blocks.** Sources are libraries; no standalone entry points.
- **Dummy parameters** added solely to satisfy the config GUI. If a parameter has no use, drop it.
- **Unsupported language codes in `PARAM_DESCRIPTIONS`, `PARAM_TRANSLATIONS`, or `HOW_TO_GET_ARGUMENTS_DESCRIPTION`.** Only `en`, `de`, `it`, `fr` are valid keys. Including any other code (e.g. `lt`, `nl`, `pl`) fails `test_source_has_necessary_parameters`. If a contributor wrote their `HOW_TO_GET_ARGUMENTS_DESCRIPTION` in only one language (e.g. `{"en": "..."}`) that is fine — do not add translations for the other languages. See the [HOW_TO_GET_ARGUMENTS_DESCRIPTION rules](#how_to_get_arguments_description-rules) section.
- **Editing files in the "must not hand-edit" list above** — they get overwritten by CI after merge.
- **Suppressing failures silently.** Returning `[]` on an HTTP error masks problems as "no upcoming collections".
- **Unformatted code.** Run `ruff check --fix` and `ruff format` before committing (see Commands below).
- **Raw `mdi:*` strings in `ICON_MAP`.** Use the canonical `Icons` enum (`from waste_collection_schedule import Icons`) so icons stay consistent across sources for the same logical waste category. See `custom_components/waste_collection_schedule/waste_collection_schedule/icons.py`.
- **A dedicated `tests/test_<source>.py` unit-test file.** `TEST_CASES` plus a live run of `test_sources.py -s <name> -l` is the normal, expected coverage for a source — don't add a standalone test file just because it seems thorough. Default to not adding one; add it only when absolutely necessary, i.e. logic so non-trivial (a tricky date/regex parser, say) that `TEST_CASES` genuinely cannot exercise it, and even then mock any network calls — don't hit the live API from the test. With ~600 sources, one test file per source doesn't scale, and root `pytest.ini`'s `python_files` allowlist covers only `test_source_components.py` and `test_fetch_retry.py` — anything else in `tests/` is never collected by `pytest tests/` or CI.

## HOW_TO_GET_ARGUMENTS_DESCRIPTION rules

`HOW_TO_GET_ARGUMENTS_DESCRIPTION` is an optional dict shown in the Home Assistant config flow above the input fields. It explains to users how to find the required parameter values (e.g. "Visit https://example.com and note the ID from the URL").

**Valid language keys:** only `"en"`, `"de"`, `"it"`, `"fr"` — the same set as `PARAM_TRANSLATIONS` and `PARAM_DESCRIPTIONS`. Any other key (e.g. `"pl"`, `"nl"`, `"lt"`, `"cs"`) will cause `test_source_has_necessary_parameters` to fail.

**It does not need to be provided in every language.** A contributor who only writes English or only writes their native language is perfectly valid:

```python
# Valid — only one language
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://example.com and select your street.",
}

# Also valid — contributor provided two languages
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://example.com and select your street.",
    "de": "Besuchen Sie https://example.com und wählen Sie Ihre Straße.",
}

# Invalid — "pl" is not a supported language code
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "pl": "Odwiedź https://example.com i wybierz swoją ulicę.",
}
```

**For reviewers and AI agents fixing up contributor PRs:** if a contributor has used an unsupported language code (e.g. `"pl"`), remove that key. Do not replace it by adding `"en"` unless you can write an accurate description of how to obtain the arguments — that knowledge belongs to the contributor. If you cannot write an accurate description, either remove the entire `HOW_TO_GET_ARGUMENTS_DESCRIPTION` dict or leave a comment for the contributor to provide one. Do **not** add language keys that the contributor did not originally include.

## Commands

```bash
# Run the full automated test suite
python -m pytest tests/

# Test a specific source against its TEST_CASES
cd custom_components/waste_collection_schedule/waste_collection_schedule/test
python test_sources.py -s <source_name> -l

# Format + lint before every commit — REQUIRED on every file you change
# ruff replaces black, flake8 and isort
ruff check --fix <path>
ruff format <path>

# Activate the git pre-commit hook (run once after cloning — enforces formatting automatically)
pre-commit install
```

`pre-commit run --all-files` runs the full lint suite (ruff lint + format, mypy, codespell, bandit, pyupgrade, yamlfmt).

> **AI agents:** Always run `ruff check --fix <path> && ruff format <path>` on every changed file before calling `git commit`. The pre-commit hook enforces this for human contributors; agents must do it explicitly.

> **Note:** Do not run `update_docu_links.py` in a PR branch. The `Update Documentation` CI workflow runs it automatically on every push to `master` (post-merge) and commits the generated output.

## Legacy examples (stable fixes only)

- HTML scraping (BeautifulSoup): [`source/birmingham_gov_uk.py`](custom_components/waste_collection_schedule/waste_collection_schedule/source/birmingham_gov_uk.py)
- ICS-based: [`source/stadtreinigung_hamburg.py`](custom_components/waste_collection_schedule/waste_collection_schedule/source/stadtreinigung_hamburg.py)
- JSON/REST API: [`source/toronto_ca.py`](custom_components/waste_collection_schedule/waste_collection_schedule/source/toronto_ca.py)

## Pull request checklist

1. Source module passes `test_sources.py -s <name>` against real TEST_CASES.
2. Pipeline source documentation is generated from class metadata; do not commit `doc/source/<name>.md`. Keep legacy documentation accurate when fixing an existing stable source.
3. `python -m pytest tests/` passes locally.
4. Changed files are formatted and linted with `ruff format` and `ruff check --fix`.
5. New-source PRs target `release/3.0.0` of `mampfes/hacs_waste_collection_schedule` and use `BaseSource` with recorded fixtures. Stable bug fixes target `master`; existing legacy sources need not be migrated for a fix.
6. Do **not** commit changes to `README.md`, `info.md`, `sources.json`, `source_metadata.json`, `translations/*.json`, or `doc/ics/*.md` — CI regenerates these after merge.
