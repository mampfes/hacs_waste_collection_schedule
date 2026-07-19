---
name: new-source
description: Investigate and implement support for a new waste-collection provider in hacs_waste_collection_schedule. Use when a contributor wants a council, municipality, or provider added, including shared-platform and ICS options.
---

# Add a waste-collection source

## Gather inputs

1. Establish whether the user is a contributor or an upstream maintainer if that is not already known.
2. Obtain the provider name, country, resident schedule URL, and one public known-working example input. Never request or expose the user's home address.

## Investigate

1. Spawn the `source-investigator` custom agent with the gathered inputs.
2. Ask it to return its complete Investigation Report and make no filesystem changes.
3. Present the report to the user.
4. If the provider is already supported, offer the exact shared-config change. If it is not feasible, explain the blocker and alternatives from the report.
5. For a new source, confirm the recommended ICS, API, HTML, or PDF approach before implementation when the choice is materially uncertain.

## Implement

1. Spawn the `source-implementer` custom agent with the full Investigation Report and any user decisions.
2. Tell it to write the source or shared-config change, create required documentation, lint every changed Python file, run structural tests, and live-test real `TEST_CASES` where applicable.
3. Present its Implementation Report and resolve test failures before submission.

## Prepare submission

1. Encourage `SOURCE_CODEOWNERS = ["@handle"]` for Python or `codeowners:` for ICS YAML.
2. Inspect the diff and remove generated files listed in `AGENTS.md` from the proposed change. Never run `update_docu_links.py`.
3. Run the required lint and tests from `AGENTS.md` for every changed file.
4. Guide contributor-owned branch, commit, push, and PR steps. Do not perform remote actions unless the user explicitly asks.
5. Target `mampfes/hacs_waste_collection_schedule:master` and use `Add source: <Provider Name> (<module>)` as the PR-title pattern.
