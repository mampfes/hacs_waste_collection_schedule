Guide a contributor through adding support for a new waste-collection provider, from "I want my council added" to "PR submitted to upstream".

## Step 0: confirm role and gather basics

If the user's role isn't already established this session, ask:

> "Are you a contributor working on a Pull Request, or a maintainer with write access to the upstream repo?"

If contributor (the expected case for `/new-source`), continue. If maintainer, suggest they may want to use the same command but note that the same workflow applies (maintainers just have additional review/merge tooling).

Ask the user for, if not yet provided:

- The council/provider name and country.
- A URL where a resident looks up their schedule.
- One public, known-working example input (an address from the council's documentation, a civic landmark, etc.), **never** the contributor's own address.

## Step 1: investigate

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

If the recommendation is **"not feasible"** (login wall, no public feed): explain why, and suggest alternatives: encourage them to ask the provider for a public feed, or look for a third-party aggregator. A **scanned/OCR-only or unstructured** PDF also lands here: defer it (leave the source request open under a status label) rather than hardcoding a schedule.

A **PDF-only** provider is otherwise a normal new source, not a blocker: the pipeline has reusable PDF components (`PdfTextParser` for a text list, `PdfTableParser` for a columnar/grid calendar, `PdfImageCalendar` for a colour-coded raster calendar, and `PdfLinkRetriever` for a rotating per-year URL). Treat it as a new source and continue to Step 2. See `doc/contributing_source.md` "PDF sources".

If the recommendation is **a new source**: confirm with the user that the approach (ICS YAML / Python source / etc.) matches their understanding. Then continue to Step 2.

New Python sources are written on the `BaseSource` pipeline platform (declare retrieve, parse, preprocess and transform from reusable components; the only source-specific code is usually `__init__`). The authoritative guide is `doc/contributing_source.md`, and `doc/new_source_template.py` is an annotated skeleton to copy from. The legacy module-level `fetch()` style is reserved for editing the roughly 600 existing legacy sources, not for new work.

## Step 2: implement

Spawn the `source-implementer` agent with the investigation report:

```
subagent_type: source-implementer
description: Implement <module name>
prompt: |
  Implement <module name> for hacs_waste_collection_schedule using the
  recommendation below:

  <PASTE THE FULL INVESTIGATION REPORT>

  Write a BaseSource pipeline source (see doc/contributing_source.md): declare
  the retrieve / parse / preprocess / transform steps from reusable components,
  set self._params and self._headers in __init__, no ICON_MAP, no fetch().
  Follow your standard step-by-step: write the source, lint, run
  tests/test_source_components.py, run test_sources.py live. Iterate until the
  test cases return non-empty collections.
```

Present the implementation report.

If `test_sources.py` returned errors, work through them with the user. The implementer's "Open questions" section often points at what to adjust.

## Step 3: submit the PR

Before the contributor stages their files, remind them:

> **Take ownership of your source.** Adding your GitHub handle as a code owner means you will be automatically notified and assigned when bug reports are filed for your source. This is how the project keeps sources healthy. It is optional but strongly encouraged.
>
> Pipeline (BaseSource) source: add `SOURCE_CODEOWNERS = ["@your-github-handle"]` as a class attribute.
> Legacy module-level source: add `SOURCE_CODEOWNERS = ["@your-github-handle"]` near the top of the `.py` file.
> ICS YAML: add a `codeowners:` key listing your handle.

The contributor handles the git steps themselves (you can guide). Walk them through:

1. **Check the diff is clean** (no generated files). Quick check:
   ```bash
   git diff $(git merge-base upstream/master HEAD)..HEAD --name-only
   ```
   Expected files:
   - `custom_components/waste_collection_schedule/waste_collection_schedule/source/<module>.py`
   (Plus an `.i18n/` directory or YAML if the source needs custom translations.)

   For a pipeline (BaseSource) source, `doc/source/<module>.md` is generated by CI from the class metadata, so it should NOT be in the diff. Only a legacy module-level source needs the doc page committed by hand.

   If anything else appears (README.md, info.md, sources.json, translation JSONs, generated doc pages, doc/ics/*.md), revert:
   ```bash
   git checkout upstream/master -- <file>
   ```

2. **Create a feature branch** (if not already on one):
   ```bash
   git checkout -b feat/add-<module>
   ```

3. **Commit** (a pipeline source is the `.py` only; a legacy source also stages `doc/source/<module>.md`):
   ```bash
   git add custom_components/.../source/<module>.py
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
- Don't run `update_docu_links.py`. CI handles it post-merge.
- A maintainer will review. They may push small fixes (style, doc tweaks) directly to the contributor's branch; that's normal.

## Step 4: follow-up

Once the PR is open, the conversation usually ends. If the maintainer requests changes via review, the contributor returns and can re-run `/new-source` (it picks up where they are) or directly use the `source-implementer` agent with the requested change.
