## Summary

<!-- What does this PR do? -->

## Type of change

- [ ] New source
- [ ] Bug fix / source fix
- [ ] Migration of an existing source to the 3.0.0 pipeline
- [ ] Documentation update
- [ ] Other

## Checklist

- [ ] `python -m pytest tests/test_source_components.py -q` passes
- [ ] `ruff check --fix` and `ruff format` run on changed source files
- [ ] No generated files in diff (README.md, info.md, sources.json, translations/*.json, CI regenerates these post-merge)
- [ ] `doc/source/<name>.md` created for new legacy sources (pipeline sources generate theirs)
- [ ] TEST_CASES use real, publicly accessible addresses (not my own)

## New or migrated pipeline sources

Skip this section only for a fix to an existing legacy `fetch()` source.

- [ ] **Cassette recorded.** `python tests/record_fixtures.py <module>`, with the resulting `tests/fixtures/<module>/*.json` committed so CI replays this source offline. One per distinct response shape for a shared-service source. If the provider genuinely cannot be recorded (geo-block, per-request challenge, credentials), say which and why in the summary.
- [ ] **Composes shared components.** No `Retriever`/`Parser` subclass defined in the source module, no `retrieve` / `parse` / `preprocess` / `transform` override on the `Source` class, and no module-level function issuing the provider's HTTP (`source.session.get/post` inside a `prepare=` / `fetch=` / `steps=` callback is a retriever written as a function).
- [ ] **Anything the platform was missing was added to the shared component** under `waste_collection_schedule/service/`, so every provider on that platform gets it, rather than being written inside this source.

A source that still needs its own step is not migrated: it has moved provider behaviour somewhere the next provider on that platform cannot reach. If you cannot avoid one, do not add it quietly. Explain in the summary what the component is missing.

<!--
Enforced in CI by tests/test_new_architecture.py:
  test_pipeline_sources_ship_a_cassette
  test_pipeline_sources_reuse_shared_components
  test_pipeline_sources_do_not_hand_roll_retrieval
  test_no_new_source_local_step_overrides
Their allowlists are debt registers for sources converted before these rules
existed, with a target of zero. They are not a place to add new work.
See doc/contributing_source.md, "Anti-patterns" and "Offline fixtures".
-->
