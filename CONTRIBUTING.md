<img src="/images/icon.png" alt="Waste Collection Schedule logo" title="Waste Collection Schedule" align="right" height="60" />

# Contributing To Waste Collection Schedule

![python badge](https://img.shields.io/badge/Made%20with-Python-orange)
![github contributors](https://img.shields.io/github/contributors/mampfes/hacs_waste_collection_schedule?color=orange)
![last commit](https://img.shields.io/github/last-commit/mampfes/hacs_waste_collection_schedule?color=orange)

There are several ways of contributing to this project, including:

- Providing new service providers
- Updating or improving the documentation
- Helping answer/fix any issues raised
- Join in with the Home Assistant Community discussion

## Adding New Service Providers

### Fork And Clone The Repository, And Checkout A New Branch

In GitHub, navigate to the repository [homepage](https://github.com/mampfes/hacs_waste_collection_schedule). Click the `fork` button at the top-right side of the page to fork the repository.

![fork](/images/wcs_fork_btn.png)

Navigate to your fork's homepage, click the `code` button and copy the url.

![code](/images/wcs_code_btn.png)

On your local machine, open a terminal and navigate to the location where you want the cloned directory. Type `git clone` and paste in the url copied earlier. It should look something like this, but with your username replacing `YOUR-GITHUB-USERNAME`:

```bash
git clone https://github.com/YOUR-GITHUB-USERNAME/hacs_waste_collection_schedule
```

Before making any changes, create a new branch to work on.

```bash
git branch <new_branch_name>
```

For example, if you were adding a new provider called abc.com, you could do

```bash
git branch adding_abc_com
```

For more info on forking/cloning a repository, see GitHub's [fork-a-repo](https://docs.github.com/en/get-started/quickstart/fork-a-repo) document.

### The 2 Ways of adding support for a new Service Provider

There are 2 ways to add support for a new service provider:

1. [Via the generic ICS source](doc/contributing_ics.md)

   This is the preferred way of adding support for a new service provider, but only works if the service providers offers a so called "ical / webcal subscription" or at least a static link which doesn't change over time to an ICS file.

2. [Dedicated source](doc/contributing_source.md)

   This is the fallback if the preferred way via the generic ICS source doesn't work.

   New dedicated sources should use the `BaseSource` pipeline. You subclass `BaseSource` and declare which standard, reusable steps to use (retrieve, parse, preprocess, transform) as class attributes; for most providers the only source-specific code is `__init__`. This removes most of the boilerplate (no hand-written `fetch()`, no per-source icon map, no manual date parsing) and reuses tested components. The older module-level `fetch()` style still works and powers most of the ~600 existing sources, so a bug fix to one of those does not need converting, but please prefer the pipeline for anything new. The [dedicated source guide](doc/contributing_source.md) is the full reference: the pipeline, the reusable retrievers / parsers / transformers, the canonical waste types, and the reusable service platforms (ArcGIS, RiSKommunal AT, AchieveForms / FirmstepSelfService, IntraMaps, Abfallnavi / regio iT, Sitepark IES, Pozi, WhatBinDay, Sepan, Junker app, A Region, Ecoharmonogram, Cloud9 apps, and the whole ICS platform) worth checking before you write any new code.

### Example Implementations

If you want to contribute a new source, these existing implementations can be used as practical examples:

- **HTML parsing (BeautifulSoup / bs4):** [`birmingham_gov_uk.py`](/custom_components/waste_collection_schedule/waste_collection_schedule/source/birmingham_gov_uk.py)
- **ICS-based implementation:** [`stadtreinigung_hamburg.py`](/custom_components/waste_collection_schedule/waste_collection_schedule/source/stadtreinigung_hamburg.py)
- **JSON/API implementation:** [`toronto_ca.py`](/custom_components/waste_collection_schedule/waste_collection_schedule/source/toronto_ca.py)

For the full list of pipeline building blocks and worked pipeline examples, see the [dedicated source guide](doc/contributing_source.md).

### Using AI coding assistants

If you're using an AI assistant (Claude Code, Cursor, codex, Aider, GitHub Copilot, etc.) to draft a contribution, point it at the project-specific instruction files in the repo:

- [`CLAUDE.md`](/CLAUDE.md) — read by Claude Code. Project overview, source module contract, common pitfalls, and pointers to the specialised agents and slash commands.
- [`AGENTS.md`](/AGENTS.md) — read by Cursor, codex, Aider, and other tools that support the `AGENTS.md` convention.
- [`.github/copilot-instructions.md`](/.github/copilot-instructions.md) — used by GitHub Copilot.

All three capture the source module contract, the lint/test commands, and the patterns that reviewers consistently flag — they help the assistant produce a PR that's much closer to mergeable on the first pass.

**Claude Code users:** the repo also ships with specialised agents and a slash command to walk you through implementing a source from scratch:

- `/new-source` — orchestrated walkthrough: confirms the provider isn't already supported, identifies the best data feed (ICS / JSON API / HTML / PDF), generates the source module + doc page, lints, and runs the test cases. Reduces the round-trip with reviewers.
- The underlying agents (`source-investigator`, `source-implementer`) can also be invoked directly if you prefer step-by-step control. See [`.claude/agents/`](/.claude/agents/) for the full list.

### Sync Branch and Create A Pull Request

Having completed your changes, sync your local branch to your GitHub repo, and then create a pull request. When creating a pull request, please provide a meaningful description of what the pull request covers. Ideally it should cite the service provider, confirm the `.py` and `doc/source/<name>.md` files have been added, and include the output of the `test_sources.py` script demonstrating functionality. Note: `README.md` and `info.md` are **auto-generated by CI after merge** — do not edit or include them in your PR. Once submitted a number of automated tests are run against the updated files to confirm they can be merged into the master branch. Note: Pull requests from first time contributors also undergo a manual code review before a merge confirmation is indicated.

Once a pull request has been merged into the master branch, you'll receive a confirmation message. At that point you can delete your branch if you wish.


## Source Ownership Mapping (Issue Routing)

To route source-related bug reports to the right maintainer, this repository uses a generated owner mapping file:

- `.github/source_owners.json` (generated by `update_docu_links.py` — do not edit manually)

A GitHub Action (`.github/workflows/notify-source-owners.yaml`) reads the `Source Name` field from `[Source Defect]` bug reports and pings plus assigns the configured owner(s) for that source.

**Per-source owners for Python sources** are defined via the optional `SOURCE_CODEOWNERS` variable in the source file:

```python
SOURCE_CODEOWNERS = ["@your-github-handle"]
```

**Per-provider owners for ICS YAML providers** are defined via the optional `codeowners` key in the YAML file:

```yaml
codeowners:
  - "@your-github-handle"
```

Every handle must start with `@` — the CI test suite enforces this. `update_docu_links.py` normalises handles (prepending `@` if missing) before writing `source_owners.json`.

If you add or maintain a source, **strongly consider adding your GitHub handle** to take ownership. You will be automatically notified and assigned on bug reports for that source, making it easier to keep your source healthy.

## Update Or Improve The Documentation

Non-code contributions are welcome. If you find typos, spelling mistakes, or think there are other ways to improve the documentation please submit a pull request with updated text. Sometimes a picture paints a thousand words, so if a screenshots would better explain something, those are also welcome.

## Help Answer/Fix Issues Raised

![GitHub issues](https://img.shields.io/github/issues-raw/mampfes/hacs_waste_collection_schedule?color=orange)

Open-source projects are always a work in progress, and [issues](https://github.com/mampfes/hacs_waste_collection_schedule/issues) arise from time-to-time. If you come across a new issue, please raise it. If you have a solution to an open issue, please raise a pull request with your solution.

### Assigning an issue to yourself

To help prevent duplicate work, we encourage contributors to self-assign issues they are actively working on (e.g. adding a specific waste collection source). To assign an open issue to yourself, simply leave a comment on the issue containing `/assign-me` — our GitHub automation will then assign it to you. Comment `/unassign-me` to release it again.

## Join The Home Assistant Community Discussion

![Community Discussion](https://img.shields.io/badge/Home%20Assistant%20Community-Discussion-orange)

The main discussion thread on Home Assistant's Community forum can be found [here](https://community.home-assistant.io/t/waste-collection-schedule-framework/186492).
