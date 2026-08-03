# v3 cleanup campaign: remove source-local pipeline steps

Working document for the migration. Delete it when the count reaches zero.

## What this is

Some sources subclass `BaseSource` but still define their own `retrieve`, `parse`,
`preprocess` or `transform`. That is provider behaviour sitting where the next
provider on the same platform cannot reach it, so the same logic gets written
again, slightly differently, and the two drift. Those sources are on the
pipeline but they are not migrated.

The campaign moves that behaviour into the shared components under
`waste_collection_schedule/service/` (and the shared retrievers, parsers,
preprocessors and transformers modules) until the count is zero.

Start from the current numbers, never from this file:

```bash
python tools/arch_coverage.py --debt
```

At the time of writing, on `release/3.0.0`: 202/959 migrated, 263 on the
pipeline, 61 carrying their own steps. The campaign opened at 113.

## Why it is safe

Almost every source in the backlog ships a cassette, so each refactor is
verifiable offline with no live provider call and no judgement:

```bash
pytest tests/test_offline_fixtures.py -k <module>
```

The recorded requests and the parsed output must be identical before and after.
If replay changes, the refactor changed behaviour and is wrong. That is the
whole safety property, and it is why this campaign is mechanical rather than
risky.

For a change to a widely shared component, the per-source replay is not enough
on its own. Dump every collection from every cassette before and after and diff
them. One agent did this across all 674 recordings for an unconditional change
to the ICS repair path, and that diff, not the passing test count, is what made
the change reviewable.

### Where the safety property does not hold: POST bodies

Replay proves less than it looks for a source that POSTs. `tests/cassette.py`
matches on an exact key (method, url and a body hash) and then falls back to
matching on method and url alone, and a recorded interaction does not store the
request body. So when a refactor changes a POST body, the key misses, the
fallback matches anyway, and the test goes green having checked nothing about
what was sent. There are 859 POST interactions across 92 sources.

This is tracked as #7102 and should be fixed in the harness. Until it is, a
migration that touches how a request is built must compare the outgoing bodies
by hand, by instrumenting the session layer, and say so in the PR. An agent
doing the Athos wizard did this unprompted and hash-matched three POST bodies
field-for-field; that is the standard, not a bonus.

## Sources with no cassette

Eight sources in the backlog have none, and cannot be verified by replay. Do
not assume the reason: probe first, because the grouping has been wrong before.
`berdorf_lu` and `kumberg_gv_at` were both listed as unreachable, both recorded
cleanly on the first attempt, and are now migrated.

```bash
python tests/record_fixtures.py <module>   # needs the live provider to be up
```

If it records, commit the cassette on its own first, so it captures today's
behaviour rather than the refactor's, then migrate normally.

If it does not record, the reason decides what happens next:

| Reason | Sources | Where it is tracked |
|---|---|---|
| Unreachable from AU | `bielefeld_de`, `erlangen_hoechstadt_de`, `regioentsorgung_de` | #7051 |
| Unreachable from AU | `fuquay_varina_nc_us` | #7052 |
| Unreachable from AU | `fredrikstad_no` | #7055 |
| Unreachable from AU | `shawinigan_ca` | #7056 |
| Stale test data, not a geo-block | `data_umweltprofis_at` | #7095 |
| Records, but does not replay deterministically | `nemaffaldsservice_kk_dk` | #7046 |

Add any new finding to the matching issue rather than starting a new one, and
say which failure you saw. "Connect timeout to `<host>`" is useful to a
contributor in-region; "could not record" is not.

### Migrating without a cassette

Waiting for a contributor in-region can take months, and these sources should
not hold the campaign open. Migrate them, but the definition of done changes,
because there is no replay to lean on:

1. **The moved code must be identical, not equivalent.** Move the body, do not
   rewrite it while it is in your hands. A tidy-up in the same commit is what
   turns an unverifiable refactor into an unverifiable rewrite.
2. **Unit-test the shared component directly.** Feed it a synthetic input that
   exercises the behaviour you moved, and assert the output. This is the only
   executable evidence the change carries, so it is not optional. Put it with
   the component's other tests, not in the source's.
3. **Every other provider on that platform must still replay.** They have
   cassettes even though this one does not, and they exercise the same code
   path you just changed.
4. **Say so in the PR,** and link the tracking issue from the table above, so
   whoever records the cassette later knows to check this migration with it.

Never fabricate a cassette by hand. A recording that was not recorded is worse
than none: it will replay green forever while proving nothing.

## Order of work

Band by the largest override in each source. Do the small band first. It is
quick, and it teaches you which component options are missing before you meet
the hard cases:

- **8 lines or fewer.** Usually param injection or a one-line filter.
- **9 to 25 lines.** Usually a missing component option.
- **Over 25 lines.** Real platform gaps. Do these last, when the component
  vocabulary is richer.

Group by platform within a band. The first batch found all five AchieveForms
`preprocess` bodies were textually identical, which one agent spots and five
agents each solve separately.

## Definition of done, per source

1. No `retrieve` / `parse` / `preprocess` / `transform` on the `Source` class,
   and no `Retriever`/`Parser` subclass in the source module.
2. Whatever the source needed now exists in the shared component, with a
   sensible default so existing providers on that platform are unaffected.
3. `pytest tests/test_offline_fixtures.py -k <module>` passes, and every other
   provider on that platform still replays. If the source has no cassette, the
   substitute rules above apply instead.
4. The source's name is deleted from `SOURCES_WITH_LEGACY_STEP_OVERRIDES` in
   `tests/test_new_architecture.py`. That deletion is the completion signal.
5. `python tools/arch_coverage.py` shows the migrated count up by one.

Never add a name to an allowlist. If a source seems to need its own step, the
component is missing a capability: that is the finding, and it belongs in the
component.

## Definition of done, per platform improvement

The campaign keeps turning up a better way to write something, not just a source
in the wrong shape. When it does, cleaning the existing sources is only part of
the job, because the next contributor writes from the documentation rather than
from the cleaned sources. A platform improvement is done when all four hold:

1. The existing sources are converted, or the ones that cannot be are listed
   with the reason they resisted.
2. **Every instruction that taught the old way is corrected**: the reference
   (`doc/contributing_source.md`), the skeleton people copy
   (`doc/new_source_template.py`), the agent (`.claude/agents/source-implementer.md`),
   the command (`.claude/commands/new-source.md`), `CLAUDE.md`, and the relevant
   docstring in the library. Grep for the old form; do not work from memory.
   Worked examples matter most, since they are what gets copied.
3. A test gate rejects the old way, so the correction does not rely on anyone
   remembering it. Prefer a gate with no exceptions: make it narrow enough to be
   provably safe rather than broad with an allowlist.
4. Anything non-obvious that was learned on the way is written down, especially a
   trap that made some sources unsafe to convert. That is the part nobody can
   rediscover from the diff.

`test_pipeline_sources_dont_redeclare_init` and the commit that added it are the
worked example: 97 sources cleaned, six instruction sites corrected, one gate at
zero exceptions, and the two rules that made the other 101 sources resist written
down (`ConfigParam.defaults` being independent of `required`, and coercion
belonging on the `ConfigParam`).

The third in the sequence found the same failure in the config fields rather than
the constructor: the `ADDRESS` term carried labels in five languages while 47
sources hand-wrote "Street Address" in English, and one source had found
`term=ADDRESS`. A concept nobody knows about is a concept nobody uses, so
`test_pipeline_sources_bind_standard_field_terms` now rejects a `text_field`
whose label duplicates a term's. It also turned up `DISTRICT` and `COUNTY` both
labelled "District" in English while their German labels (`Ortsteil` against
`Landkreis`) meant opposite ends of the hierarchy: a coin flip dressed as a
choice. Look for that shape. A vocabulary with two entries for one word, or one
entry nothing references, will be got wrong.

The second follow-up is worth reading alongside all of this, because it shows
point 4 cutting the other way. Rather than live with the first of those two rules, the next change
removed it: `apply_defaults` now fills every optional field with `None`, so the
documented trap became a documented guarantee and 33 more sources lost their
`__init__`. When a trap turns out to be fixable, fix it and correct the note; a
faithfully documented trap is still a trap.

## Running it

Work in the devcontainer, which matches the CI minimum lane. Verify with the
pinned hooks, never bare linters:

```bash
pytest
pre-commit run --all-files
```

A bare `pyright` resolves a different type-stub set and reports a different
error list from CI. That is how three errors reached CI in #7089.

`pytest` now means the gating CI lane. Since #7092, `pytest.ini` carries
`addopts = -m "not live"`, so the live-provider tests are deselected by
default. Before that a plain run sat on real HTTP for over ten minutes and two
agents lost time to it. Run `pytest -m live` when you actually want the live
lane.

Occasionally, and before pushing anything that touches a shared component:

```bash
.devcontainer/check-current.sh    # reproduces the CI latest-HA lane
```

### Parallel agents

One agent per platform group, each in its own git worktree, roughly six at a
time. Three things bite:

- **Verify the base, every time.** Agent worktrees are cut from the repository's
  default branch, which is `master`, not from whatever you have checked out.
  This is the default behaviour and not an occasional slip. Create the
  worktrees yourself from the branch tip and have each agent confirm with
  `git merge-base --is-ancestor <branch-tip> HEAD` before it does anything.
- **Serialise same-component work.** Two agents extending the same service
  module will conflict. Group by platform, give one agent the whole group, and
  tell each agent which module it owns and who owns the rest. An agent that
  knows it is borrowing someone else's file will say so, or move its change
  somewhere better. One ICS agent, told `parsers.py` was not its file, reverted
  a change it had already made there and rebuilt it in `service/ICS.py`
  composing the shared parser, which was the better design anyway.
- **Split the batch on "does it override `retrieve`".** Platform grouping alone
  still let two agents collide in `preprocessors.py`. Giving one agent only
  sources with no `retrieve` override lets it own `parsers.py` and
  `preprocessors.py` outright while another owns `retrievers.py`, and the
  collisions stop.
- **Hand a deferral on as a claim, not a fact.** When an agent defers a source
  and explains why, the next agent must verify that reasoning rather than
  design around it. Of four documented reasons `awg_de` could not be migrated,
  two were wrong: an "unavoidable" multipart body returned a byte-identical
  calendar when sent urlencoded, and a per-`Zeitraum` fan-out turned out to
  reference a string that appears in no response, live or recorded, so that
  code path had never run.
- **Agents lose their turn, not their work.** A dropped connection or a
  restarted process leaves the worktree edits in place and uncommitted. Check
  `git status` in the worktree before assuming anything was lost, and resume
  the agent rather than starting again.

Collect results by cherry-picking each agent's commit onto the batch branch,
then run the full verification on the combined tree. The component changes have
not met each other until that point.

Expect a conflict in `tests/test_new_architecture.py`, where every agent
deletes its own names from the same allowlist. It resolves automatically in
most cases and is trivial when it does not.

### Agent prompt template

> Your working directory is the worktree at `<PATH>`, on branch `<BRANCH>`.
> Every command and every path must be inside it. Confirm the base first with
> `git merge-base --is-ancestor <TIP> HEAD` and stop if it fails.
>
> `source/<MODULE>.py` subclasses `BaseSource` but defines its own `<STEPS>`.
> Move that behaviour into the shared component so every provider on the
> platform gets it, and leave the source declarative: metadata, `PARAMS`,
> `REGIONS`, `TEST_CASES`, and a composition of shared steps.
>
> Rules:
> 1. No `Retriever`/`Parser` subclass in the source module, and no step method
>    on the `Source` class. Do not add the source to any gate allowlist.
> 2. Anything the platform lacks goes into `waste_collection_schedule/service/`
>    (or the shared retrievers/parsers/preprocessors/transformers), with a
>    default that leaves existing providers unchanged.
> 3. You own `<MODULES>`. Other agents own the rest. If you must edit one of
>    theirs, do it and say so prominently in your report.
> 4. This is a refactor. Behaviour must not change.
>
> Verify: `pytest tests/test_offline_fixtures.py -k <MODULE>` must pass with
> the recorded cassette unchanged, `git status --short tests/fixtures/` must be
> empty, and every other provider on the same platform must still replay. Then
> `pytest` and `pre-commit run --all-files`. Finally delete `<MODULE>` from
> `SOURCES_WITH_LEGACY_STEP_OVERRIDES` in `tests/test_new_architecture.py`.
>
> Commit on your branch. Do not push, do not open a PR. Report the commit,
> which shared components you used, exactly what you added to the platform
> layer, and confirmation that the cassettes replay unchanged.

## Pull requests

- Base every PR on `release/3.0.0`, never `master`.
- Tag every PR with the **3.0.0 milestone**.
- **Stack the next batch on the last one** rather than waiting for a merge. It
  is what lets each batch extend the components the previous batch added
  instead of reinventing them: by batch 4 two ICS sources migrated with no new
  component at all.
- **Expect a conflict when the PR below is squash-merged,** and do not be
  alarmed by it. Squashing puts one new commit upstream while the stacked
  branch still carries the originals: same tree, different SHAs, so git reports
  a conflict on every line. Fix it with
  `git rebase --onto upstream/release/3.0.0 <old-base>`, which drops the
  already-merged commits cleanly because the trees match. There is normally
  nothing to resolve by hand. Only a squash that included review edits will
  need real merging.
- One PR per batch of roughly eight sources, grouped by platform where
  possible, so a reviewer sees the component change and its consumers together.
- Title: `refactor(v3): move <platform> behaviour into the shared component`.
- Say in the body how many names left the allowlist and what the coverage
  number moved to, and call out the widest-reaching hunk so it gets read.

## Watch for

- **A component option that only one source will ever use.** That is a source
  masquerading as a platform feature. Prefer a narrow, well-named option over a
  general one nobody else can use, and say so in the PR.
- **An override that was never needed.** `wermelskirchen_de` had one that did
  nothing the shared parser did not already do. Check before you design a
  component around it.
- **A source bypassing the transformer layer.** `api_hubert_schmid_de` was
  hardcoding a `WasteType` in `classify()`. If you are in the file anyway, that
  belongs in a `type_value_map`.
- **`None` header values.** `curl_cffi` reads `None` as "suppress this default
  header"; plain `requests` has no such concept, which is what
  `_plain_headers` in `retrievers.py` exists for. Do not "simplify" it away.
- **Cassette churn.** A diff that rewrites recorded fixtures is a behaviour
  change wearing a refactor's clothes. Recorded requests should be untouched,
  and `git status --short tests/fixtures/` is the check.
