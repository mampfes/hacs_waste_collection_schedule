# v3 cleanup campaign: remove source-local pipeline steps

**The count reached zero on 2026-08-06.** 263 of 263 pipeline sources are fully
declarative and `SOURCES_WITH_LEGACY_STEP_OVERRIDES` is an empty set.

**And then it turned out the count was measuring the wrong thing.** #7139 found
that "fully declarative" meant "no step *method* and no step *class*", so 28 of
those 263 sources still issue the provider's HTTP from a module-level function
handed to a component. `tools/arch_coverage.py` now reports that as its own
line, and `SOURCES_HAND_ROLLING_RETRIEVAL` in `tests/test_new_architecture.py`
is the register. Zero on the old measure still stands; it just means less than
it read as. Whoever picks this up next should decide whether the second number
is the campaign's business or a successor's, because clearing it means new
components rather than moved code.

This file said to delete it at zero. Do not delete it yet, and do not keep it as
it stands. Most of it is scaffolding that has served its purpose, but four
things in it are hard-won and recoverable from nowhere else: the substitute
rules for migrating a source with no cassette, the "definition of done, per
platform improvement", the parallel-agent lessons, and the "watch for" list.
Those belong in `doc/contributing_source.md`, which is where the next
contributor actually looks. Rehome them, then delete this file. That is the last
task of the campaign, and it is the one point 4 of its own definition of done
demands.

Everything below is kept for that rehoming pass and for the archaeology of how
the count moved from 113 to zero. The numbers in it were current when written.

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

At the time of writing, on `release/3.0.0`: 255/959 migrated, 263 on the
pipeline, 8 carrying their own steps. The campaign opened at 113.

Those last 8 are the whole remaining backlog, and they are not a random tail.
Seven of them are the sources that cannot be recorded (the table below), so they
were skipped by every batch that leaned on replay, and the eighth is `ics`
itself, which is the platform rather than a provider on it. Read "Migrating
without a cassette" before starting any of the seven.

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

Check *which* cases replay before leaning on that. A source's cassette directory
holding a recording does not mean all of its `TEST_CASES` are recorded, and until
#7135 nothing checked the difference: `abfall_io_graphql` had seven of eleven
cases unrecorded, `ics` five of nine. `CASES_AWAITING_CASSETTE` in
`tests/test_new_architecture.py` is the list. A `-k <module>` run that only
exercises two of ten cases proves the refactor safe for two of ten cases.

For a change to a widely shared component, the per-source replay is not enough
on its own. Dump every collection from every cassette before and after and diff
them. One agent did this across all 674 recordings for an unconditional change
to the ICS repair path, and that diff, not the passing test count, is what made
the change reviewable.

### Where the safety property does not hold: what a cassette pins

Replay proves less than it looks, and not only for a source that POSTs.
`tests/cassette.py` matches on an exact key (method, url and a body hash) and
then falls back to matching on method and url alone. A recorded interaction did
not store the request body, so when a refactor changed what was sent, the key
missed, the fallback matched anyway, and the test went green having checked
nothing.

The measured exposure on `5ddeff3f`, over 682 cassettes and 2,535 recorded
interactions:

| | interactions | sources |
|---|---|---|
| POST | 870 | 93 |
| any payload hashed into the key but not stored (POST bodies and GET query strings alike) | 1,768 | 202 |

The second row is the real figure. A GET is not safer than a POST here: its
`params` go into the hash, and the first fallback candidate is the bare url,
which ignores them entirely. A run of the real gate with a plugin adding one
junk field to every outgoing request passed 679 of 682 replays with 1,634
deliberately altered requests, and 108 of 108 GET-only sources passed with a
changed `params`.

Two details worth knowing:

- **`_body_hash` returns on the first of `json`, `data`, `params` that is
  present.** A source sending `params=` beside a `json=` body had its params in
  neither the key nor anywhere else, so changing them was invisible even in
  principle.
- **The fallback takes the first *unused* match, so requests sharing a URL are
  paired positionally.** This is worse than "a change is not noticed": a changed
  body can be handed the response recorded for a *different* request. `awg_de`
  POSTs three times to one servlet URL and replays entirely that way.

#### What is fixed, and what is not

A recorded interaction now stores a `body`: every payload slot at once (`json`,
`data`, `params`, `files`), canonically rendered so key order cannot matter and
so `data={"a": 1}`, `data="a=1"` and a prepared `b"a=1"` all render the same.
Replay compares it and fails loudly, printing recorded against sent.

The change is **additive**, and that limit matters more than the fix. A cassette
with no `body` field keeps replaying exactly as it did, because seven pipeline
sources cannot be recorded from this location at all (see the table below) and a
fix that forced a re-record would strand them permanently. So **nothing already
committed gained anything**: of the 2,476 requests a full replay serves, 341
still match on the loose fallback, across 120 of the 682 cassettes, and 31
cassettes pin nothing whatsoever.

Two gates in `tests/test_offline_fixtures.py` hold that remainder, and it takes
two because one number cannot do both jobs:

- `UNPINNED_INTERACTIONS` counts recorded interactions with no stored body. It
  is a static property of the committed fixtures, so it is exact, and only a
  re-record moves it. **That is the ratchet: lower it every time you re-record.**
- `FALLBACK_BUDGET` caps how many requests a full replay serves off the
  fallback. It catches what the static count cannot, a cassette that carries
  bodies but still falls back, which is what a request-building regression looks
  like.

Do not tighten `FALLBACK_BUDGET` to the last unit. Measured repeatedly over the
full tree it lands between 338 and 341, because two sources do not issue
identical requests twice: `app_abfallplus_de` puts a fresh `uuid4` in its POST
body, and `lobbe_app` varies by one on three cassettes. The ceiling carries a
margin of that order and no more.

Re-record opportunistically: when you touch a source with a cassette,
`python tests/record_fixtures.py <module>` gives it request bodies and lets you
lower `UNPINNED_INTERACTIONS`.

**Re-recording is not universally safe, and this is the trap to know about.** A
source that puts a value in its request that changes from run to run cannot be
pinned. Once its cassette stores a body, replay compares that body, and the
recorded random value will never be sent again. `app_abfallplus_de` is exactly
this: `AppAbfallplusDe._client` is a fresh `uuid4` that goes into the POST body.
Its cassettes replay today only because nothing is compared. Re-record one and
it stops replaying at all. That is a true finding about the source rather than
about the harness, and the fix belongs in the source, deriving the value
deterministically (the clock is safe, because replay freezes it), not in
loosening the matcher. Check for a nonce, a uuid or a wall-clock stamp in the
request before re-recording, and if there is one, leave the cassette alone and
say so.

`ecoharmonogram_pl` is the second one found, so this is a shape rather than a
one-off: `EcoHarmonogramPL` puts `hex(randrange(...))` in every POST as
`clientId`, and its 14 cassettes (88 interactions) cannot be pinned until the
source derives that value deterministically. Both were found the same way, by
diffing two `tests/dump_requests.py` runs of the *same* code and noticing a
field that moved on its own. Do that before crediting any diff to your change.

Until a source's cassette carries bodies, a migration that touches how a request
is built must still compare the outgoing requests by hand:

```bash
python tests/dump_requests.py <module> > before.txt
... refactor ...
python tests/dump_requests.py <module> > after.txt
diff before.txt after.txt
```

An agent doing the Athos wizard did this unprompted and hash-matched three POST
bodies field-for-field; that is the standard, not a bonus.

To check whether a cassette pins anything at all, run the gate against
`tests/mutate_requests.py`, which alters every outgoing request:

```bash
python -m pytest tests/test_offline_fixtures.py -q -p tests.mutate_requests
```

Anything still passing there checked nothing about what it sent. A failure here
is the good outcome: it means the cassette noticed. The run on 2026-08-06 is 20
failed, 667 passed, 1 skipped, up from 5 failed when the gate went in, because
every re-recorded fixture joins the failing side. The `frankenberg_de` pair is
the newest addition, re-recorded with #7100. As fixtures are re-recorded that
pass count is what should keep falling.

## Sources with no cassette

Seven sources in the backlog have none, and cannot be verified by replay. Do
not assume the reason: probe first, because the grouping has been wrong before.
`berdorf_lu` and `kumberg_gv_at` were both listed as unreachable, both recorded
cleanly on the first attempt, and are now migrated. `nemaffaldsservice_kk_dk` was
listed as recording but not replaying deterministically, and now ships two
cassettes and is migrated. Three of the ten entries this table has carried were
wrong about the reason.

```bash
python tests/record_fixtures.py <module>   # needs the live provider to be up
```

If it records, commit the cassette on its own first, so it captures today's
behaviour rather than the refactor's, then migrate normally.

If it does not record, the reason decides what happens next:

All seven were re-probed on 2026-08-05 and all seven still fail, with the failure
each one gives:

| Failure seen | Sources | Where it is tracked |
|---|---|---|
| Cannot connect to host (curl 7), connect timeout on `regioentsorgung.de` | `bielefeld_de`, `erlangen_hoechstadt_de`, `regioentsorgung_de` | #7051 |
| 403 Forbidden from `gis1.fuquay-varina.org`, not a network block | `fuquay_varina_nc_us` | #7052 |
| DNS does not resolve `arcgis.fredrikstad.kommune.no` | `fredrikstad_no` | #7055 |
| Connect timeout to `geoweb.shawinigan.ca` | `shawinigan_ca` | #7056 |
| Stale test data, not a geo-block: the recorded `url` key returns no collections, and the `Rohrbach` case passes no `url` at all | `data_umweltprofis_at` | #7095 |

Add any new finding to the matching issue rather than starting a new one, and
say which failure you saw. "Connect timeout to `<host>`" is useful to a
contributor in-region; "could not record" is not. Note the failure mode can
change without the source becoming recordable: `fuquay_varina_nc_us` used to time
out and now returns 403, which is the same geo-block wearing different clothes.

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

## The last one: `ics`

`ics` is the eighth and it is not like the other seven. It is the generic,
user-configurable ICS source rather than a provider, so its `retrieve` is the ICS
platform's own retriever, driven entirely by `PARAMS` (`url` or `file`, `method`,
`year_field`, `params`, `headers`, `verify_ssl`, `impersonate`), and its `parse`
already just composes `ICS`. Nothing about it is provider-specific, which is
precisely the argument for moving it: the ~178 YAML providers it folds in, and
every future one, should reach that retriever through the shared component rather
than through this one module.

Two things make it the last one rather than the easiest:

- It replays only 4 of its 9 `TEST_CASES` (`CASES_AWAITING_CASSETTE` lists the
  other five), so the safety property is weaker here than the module's cassette
  count suggests.
- The December branch in `retrieve` fetches next year as well and swallows the
  failure, so it is dead most of the year and its behaviour cannot be observed by
  replay at all outside December. Move it, do not rewrite it.

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
   no `Retriever`/`Parser` subclass in the source module, and no module-level
   function issuing the provider's HTTP. That last one was invisible to every
   gate until #7139: a `prepare=` / `fetch=` / `steps=` callback calling
   `source.session.get` is a retriever, and `def` rather than `class` does not
   make it reusable.
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
> 1. No `Retriever`/`Parser` subclass in the source module, no step method on
>    the `Source` class, and no module-level function calling
>    `source.session.get/post`. Do not add the source to any gate allowlist.
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

  The exception is a change that *is* meant to alter a request, and it needs
  showing rather than asserting, because a re-recorded fixture is an unreadable
  diff of base64. Fixing `frankenberg_de`'s quoted street id
  (`ak_strasse="'51'"` to `ak_strasse=51`, #7100) changed the outgoing POST, so
  its two cassettes had to be re-recorded. What made that reviewable was the
  evidence either side of it: `tests/dump_requests.py` before and after, showing
  one field changed and nothing else; and the `DTSTART`/`SUMMARY` sets pulled
  out of the old and new recordings and compared, identical at 101 events each.
  Do both, and put the numbers in the PR.
- **A gate matching on packaging rather than on behaviour.** The reuse gate
  looked for a `Retriever`/`Parser` *subclass*, so the same behaviour written as
  a module-level function and handed to a component (`prepare=`, `fetch=`,
  `steps=`) was invisible to it. Two sources on one vendor module kept
  hand-rolled decoders through two migrations that way and drifted into four
  readings of one reply format (#7139, #7100). This was the third gate in a week
  that read as comprehensive while missing a whole form of the thing it checks,
  after the empty-fixture-directory cassette check and the `PARAMS`-truthiness
  membership test below. Match on the property you care about, not on a proxy
  that usually correlates with it.
- **A falsy value standing in for a missing one.** Pipeline membership was
  tested as `if not getattr(cls, "PARAMS", None)` in two gates. A zero-parameter
  source declares `PARAMS = ()`, which is falsy, so "has no params" and "is not
  on the pipeline" collapsed into one answer and 21 of the 266 pipeline sources
  sat outside the entire v3 gate suite. Fourteen of them were violating the
  waste-types gate, including `koppl_at`, which is issue #6935's own first
  example and a reference conversion in `CLAUDE.md`. The proxy also hid a fifth
  `ALL_TYPES` source nobody had counted. Membership is `issubclass(cls,
  BaseSource)`; `tools/loc_report.py` already got this right, and the tests were
  simply left behind. Look for the same shape wherever an empty collection, a
  zero, or an empty string is the legitimate value of an attribute whose
  *presence* is what is being tested. `config_flow._is_new_style_source` still
  carries this exact bug, which is tracked separately because fixing it changes
  runtime behaviour.
