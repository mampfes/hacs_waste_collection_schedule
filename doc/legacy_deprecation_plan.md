# Legacy source removal: the plan

Working document. It records what has to happen when the last legacy source is
migrated, so the compatibility scaffolding is removed deliberately rather than
discovered years later. Add to it whenever a v3 change leaves a bridge behind.

Nothing here is scheduled. Removal is a **major** version under
[`doc/versioning.md`](versioning.md), and the trigger is the legacy count
reaching zero, not a date.

## Where the count is

```bash
python tools/arch_coverage.py --debt
```

Two source styles exist. A **legacy** source is a module with `TITLE`/`URL`/...
at module level and a hand-written `fetch()`. A **v3** (pipeline) source is a
`BaseSource` subclass that declares its steps. The full contract for both is in
[`contributing_source.md`](contributing_source.md).

## Scaffolding that exists only for legacy sources

Each row is dead the moment the legacy count hits zero. None of it may be used
by a v3 source, and where a gate enforces that, it is named.

| What | Where | Enforced by |
|---|---|---|
| `EXTRA_INFO` dict list, and the `from_extra_info()` adapter that turns it into `Region`s | `regions.py`, `update_docu_links.py` | `test_pipeline_sources_do_not_use_extra_info` |
| `PARAM_TRANSLATIONS` / `PARAM_DESCRIPTIONS` per-source label dicts | source modules, `update_docu_links.py` | none yet, see below |
| `default_translations.py`, keyed by field name | library | none yet |
| `ICON_MAP` and the `Icons` enum | `icons.py`, source modules | `test_icon_map_uses_canonical_icons` (legacy only by construction) |
| `__init__` signature introspection to derive config-flow fields | `config_flow.py:829`, `update_docu_links.py:453` | the `PARAMS` fallback in both |
| `_uses_base_source_init()` and the `VAR_KEYWORD` early return | `tests/test_source_components.py`, `tests/test_new_architecture.py` | n/a, they *are* the shims |
| hand-written `doc/source/<id>.md` pages | `doc/source/` | `doc_generator.py` generates the v3 ones |
| module-level metadata reads (`getattr(module, "TITLE", ...)` and friends) | `update_docu_links.py`, `config_flow.py` | n/a |
| the `fetch()` contract itself, and `SourceShell`'s legacy branch | `source_shell.py` | n/a |

## Work to do at removal

1. Delete each row above, and the branch in every consumer that reads it. The
   `getattr(source_cls, X, None) or getattr(module, X, None)` pattern in
   `update_docu_links.py` collapses to the class read.
2. Delete the shim-aware halves of the tests, so a signature check no longer has
   to ask which style it is looking at.
3. Retire the gates whose only purpose was to stop v3 sources reaching for a
   legacy mechanism. They have no work left once the mechanism is gone.
4. Delete the hand-written `doc/source/*.md` for migrated sources, since
   generation covers them.
5. Re-check `tools/loc_report.py`'s `PIPELINE_MARKER`. It is the text
   `class Source(BaseSource)`, which misses the ten sources whose base is another
   source, so every migration figure quoted so far is slightly low. With no
   legacy sources left the marker can go entirely.
6. Announce per the deprecation lifecycle in [`versioning.md`](versioning.md): a
   runtime warning, a `CHANGELOG.md` entry, a `DEPRECATIONS.md` row, kept for at
   least two minor releases before the major.

## Gaps worth closing before then

- **`PARAM_TRANSLATIONS` has no gate.** A v3 source should never declare one:
  labels come from `field_terms.py` via `PARAMS`. Worth a gate in the same shape
  as the `EXTRA_INFO` one, so the legacy path cannot leak into new work.
- **`address_suffix` needs a `FieldTerm`.** It appears in five sources as a
  hand-written label. Blocked on de/fr/it/nl wording that a person should write.
- **Twelve sources keep an `__init__` only to default a field to `""`.**
  `apply_defaults` supplies `None`, not `""`. Either declare `default=""` on the
  param or teach those sources to read `params.get(...) or ""`.
- **The worked examples are untested code.** Twice now a doc example has been the
  thing teaching a mistake (an `__init__` skeleton that the gate now rejects, and
  `text_field("house")` where `house_number()` exists). Extracting the fenced
  Python from `contributing_source.md`, `new_source_template.py` and
  `.claude/agents/source-implementer.md` and running the source gates over it
  would close the hole cheaply.

## Decided against: authoring regions per country

Considered 2026-08-04 and rejected. Recorded so it is not re-litigated, because
it is a reasonable-sounding idea that the current design already answers.

**The proposal.** A source module would describe the mechanism only (pipeline
steps and `PARAMS`), and every region would live in an authored registry keyed by
country, e.g. `regions/<country>.yaml`, each entry naming its source and the
parameter values that select it.

**Why it is unnecessary: the separation already exists.** The config flow is
already region-first and country-keyed. Step one selects a country, step two
selects from `_SOURCES[country]`: 3,484 listings across 32 countries, each one
`{title, module, default_params, id}`. That is the proposed structure, generated
into `sources.json` rather than authored. The split in force today is

- **authored per source**, because the platform owns its provider list
- **generated per country**, because that is how a user browses

which puts each half where it belongs.

**Why authoring per country would be worse.**

1. It scatters a platform's coverage. ICS providers span DE/AT/CH and
   `abfall_io` spans DE/AT, so one platform's providers would be split across
   several country files and no file would show the platform whole. That is the
   unit a maintainer actually works in.
2. It costs ~900 listings for nothing. A single-region source needs no region
   declaration at all: its listing is built from `TITLE`/`URL`/`COUNTRY` (see
   `update_docu_links.py`, the `if title is not None` block). Country-keyed
   authoring would need an explicit entry for every one of them, making a new
   source two files instead of one.
3. It moves validation across a file boundary. Region params are validated
   against the source's `PARAMS` because they are colocated.

**The real gap, which is narrower.** A multi-region registry is authored in
*Python*: ten sources carry a `_PROVIDERS`-style literal plus a bespoke
`_regions()` comprehension. That is what makes adding a provider a code edit, and
`regions.from_yaml()` (below) fixes it without restructuring anything: authored
per source, as data, still generated per country.

## Steps that stand on their own

Each is worth doing regardless, and none depends on the rejected restructure:

1. `regions.from_yaml()` as shared scaffolding, replacing the ten bespoke
   `_regions()` comprehensions over ad-hoc `_PROVIDERS` literals and the ~60-line
   bespoke `_load_ics_yaml_regions()`. One loader, one runtime guard.
2. Generate the ICS "known supported" howto table from each file's `extra_info`.
   Today both list the same providers and CLAUDE.md documents editing **both**,
   which is the clearest instance of the problem this plan exists to remove.
3. A gate for `PARAM_TRANSLATIONS`, as above.
