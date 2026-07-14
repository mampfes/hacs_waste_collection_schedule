# Versioning and deprecation policy

This project follows **strict semantic versioning** (Option A from the RFC in
[discussion #6622](https://github.com/mampfes/hacs_waste_collection_schedule/discussions/6622)).
A release's bump is the highest-severity change it contains.

## What each digit means

| Bump | Meaning | Examples |
|---|---|---|
| **PATCH** (`x.y.Z`) | Backward-compatible fixes. "It was broken, now it works." | A bug fix to an existing source, a dependency bump, docs or CI/infra changes. |
| **MINOR** (`x.Y.0`) | Backward-compatible additions. Existing configs keep working unchanged. | A new source, a new shared platform, a new optional parameter, a new country, and any **new deprecation** (deprecating leaves the old thing working, so it is non-breaking). |
| **MAJOR** (`X.0.0`) | Breaking changes that need user action. | **Removing** a deprecated source or parameter, a config-schema change, an entity-ID change, a waste-type label change that breaks type-based filters or customisation, dropping support for an older Home Assistant version. |

Why strict SemVer, and why now: the BaseSource pipeline is what makes
"breaking versus non-breaking" precise enough for the scheme to carry signal.
Canonical `WasteType`s make a label change a well-defined breaking event, typed
`PARAMS` and response-shape validation make config and schema changes explicit,
and the componentised services make capability additions clean. A version
string now means what most consumers (and HACS) assume it means.

Deprecation visibility (the main reason to prefer the alternative content-based
scheme) is handled instead by the release-note ordering below, so we keep that
benefit without loosening the scheme.

## Migrating a source to the pipeline is a breaking change

Converting a legacy source to the BaseSource pipeline changes its waste-type
labels from the author's hard-coded strings to the canonical `WasteType` names.
Config arguments are unchanged, but type-based filters and customisation
reference the label, so a migration is a **breaking change for that source's
users** and lands in a **major** release. Because migrations arrive in batches,
they are collected behind a single major (shipped first as an
`X.0.0-alpha`/`beta`) rather than dribbled out. The legacy `fetch()` contract
stays supported indefinitely, so an individual source can revert if needed.

## Deprecation lifecycle

- **When to keep a compatibility shim.** Only when removal would change entity
  IDs or otherwise break existing user configs. If a replacement does not change
  entity IDs, replace the source cleanly rather than carrying an alias.
- **How a deprecation is announced.** A runtime warning logged once, a
  `Deprecated` entry in `CHANGELOG.md`, a note in the source's doc pointing at
  the replacement, and a row in `DEPRECATIONS.md`.
- **How long it is kept.** At least **two minor releases** before removal, and
  never removed in the same release it was deprecated in.
- **When removal beats an indefinite alias.** When the shim carries real
  maintenance cost and either the affected user base is small or the migration
  is trivial.
- **Where removals land.** Batched into the next **major** release, with a clear
  "Removed" callout.

`DEPRECATIONS.md` (repo root) tracks each deprecated item and its target removal
version, so aliases do not silently accumulate.

## Release-note ordering

CHANGELOG sections and GitHub release notes are ordered by importance to someone
updating an existing install (who is the person most likely to read them):

1. **Removed**
2. **Deprecated**
3. **Added** (sources and features)
4. **Fixed**
5. **Other** (config flow, infra, docs)

Leading with removals and deprecations gives users time to migrate before a
deprecation escalates to removal. Omit a section entirely rather than printing
an empty heading.
