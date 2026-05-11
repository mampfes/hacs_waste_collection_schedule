Guide a contributor through adding support for a new waste-collection provider, from "I want my council added" to "PR submitted to upstream".

## Step 0 — Confirm role and gather basics

If the user's role isn't already established this session, ask:

> "Are you a contributor working on a Pull Request, or a maintainer with write access to the upstream repo?"

If contributor (the expected case for `/new-source`), continue. If maintainer, suggest they may want to use the same command but note that the same workflow applies — maintainers just have additional review/merge tooling.

Ask the user for, if not yet provided:

- The council/provider name and country.
- A URL where a resident looks up their schedule.
- One public, known-working example input (an address from the council's documentation, a civic landmark, etc.) — **never** the contributor's own address.

## Step 1 — Investigate

Spawn the `source-investigator` agent:

```
subagent_type: source-investigator
description: Investigate <provider name>
prompt: |
  Investigate adding support for <provider name> (<country>) to
  hacs_waste_collection_schedule.

  Schedule lookup URL: <url>
  Example input: <example>

  Run your full investigation and return the structured recommendation.
```

Present the recommendation to the user.

If the recommendation is **"already supported via shared platform"**: explain how to add the location to the shared config (the recommendation will name the exact file). Either guide them through the one-line edit, or invoke `source-implementer` with the location-add task.

If the recommendation is **"not feasible"** (login wall, no public feed, PDF-only with no resident-facing tooling): explain why, and suggest alternatives — encourage them to ask the provider for a public feed, or to attempt the PDF approach themselves with `pypdf` (see `mpo_krakow_pl.py`).

If the recommendation is **a new source**: confirm with the user that the approach (ICS YAML / Python source / etc.) matches their understanding. Then continue to Step 2.

## Step 2 — Implement

Spawn the `source-implementer` agent with the investigation report:

```
subagent_type: source-implementer
description: Implement <module name>
prompt: |
  Implement <module name> for hacs_waste_collection_schedule using the
  recommendation below:

  <PASTE THE FULL INVESTIGATION REPORT>

  Follow your standard step-by-step: write the source, write the doc page,
  lint, run tests/test_source_components.py, run test_sources.py live.
  Iterate until the test cases return non-empty collections.
```

Present the implementation report.

If `test_sources.py` returned errors, work through them with the user — the implementer's "Open questions" section often points at what to adjust.

## Step 3 — Submit the PR

The contributor handles the git steps themselves (you can guide). Walk them through:

1. **Check the diff is clean** — no generated files. Quick check:
   ```bash
   git diff $(git merge-base upstream/master HEAD)..HEAD --name-only
   ```
   Expected files:
   - `custom_components/waste_collection_schedule/waste_collection_schedule/source/<module>.py`
   - `doc/source/<module>.md`
   (Plus an `.i18n/` directory or YAML if the source needs custom translations.)
   
   If anything else appears (README.md, info.md, sources.json, translation JSONs, doc/ics/*.md), revert:
   ```bash
   git checkout upstream/master -- <file>
   ```

2. **Create a feature branch** (if not already on one):
   ```bash
   git checkout -b feat/add-<module>
   ```

3. **Commit**:
   ```bash
   git add custom_components/.../source/<module>.py doc/source/<module>.md
   git commit -m "Add source: <Provider Name> (<module>)"
   ```

4. **Push to the contributor's fork**:
   ```bash
   git push -u origin feat/add-<module>
   ```

5. **Open the PR**:
   ```bash
   gh pr create --repo mampfes/hacs_waste_collection_schedule \
     --base master \
     --title "Add source: <Provider Name> (<module>)" \
     --body "<short summary of provider + how to obtain the parameter values + test cases used>"
   ```

Remind the contributor:

- Target branch must be `mampfes/hacs_waste_collection_schedule:master`. Not their fork's master.
- Don't run `update_docu_links.py` — CI handles it post-merge.
- A maintainer will review. They may push small fixes (style, doc tweaks) directly to the contributor's branch; that's normal.

## Step 4 — Follow-up

Once the PR is open, the conversation usually ends. If the maintainer requests changes via review, the contributor returns and can re-run `/new-source` (it picks up where they are) or directly use the `source-implementer` agent with the requested change.
