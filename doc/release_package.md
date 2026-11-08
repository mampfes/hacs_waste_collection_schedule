# Integration release package

Releases containing `zip_release: true` in `hacs.json` use the attached
`waste_collection_schedule.zip`, not GitHub's automatic source ZIP. The asset
has `manifest.json` directly at its root; neither a repository wrapper nor
`custom_components/waste_collection_schedule/` belongs inside it. HACS 2.0.5
and Home Assistant Marketplace 2026.11.0 extract release assets directly into
the integration directory.

`tools/build_release_package.py` packages every committed file in the integration
subtree plus the root MIT `LICENSE`, including translations, nested Python packages, frontend bundles and
third-party notices. Repository tests/cassettes, docs, developer frontend sources
and caches outside that subtree are not shipped. Runtime subdirectories called
`test` are deliberately retained. It does not change GitHub's automatic archives.
The builder rejects symlinks, caches, unsafe paths and Marketplace's size/member
limit violations; repeated builds of one commit have identical bytes.

## Publication

The `release: published` workflow handles stable releases and prereleases,
including prereleases published from drafts. The release tag must contain this
workflow and matching ZIP metadata. Checkout uses the release event commit SHA,
not the current branch; the manifest version must match the tag. Before upload,
the workflow verifies that the tag still points at that commit. The build job has read-only permissions; the separate upload job has
`contents: write`, with `GH_TOKEN` scoped to its upload step. A rerun accepts an identical
existing asset and fails rather than replacing different content. Never move an
existing tag or replace an existing asset to change its source.

This published-event workflow requires mutable release assets (beta9 currently
has `immutable: false`). If release immutability is enabled later, assets must be
built and attached to a draft *before* publishing, using a revised release process.

Publication and asset upload are asynchronous: there is a short interval after
a release is published before its ZIP is ready. Check the packaging workflow and
asset before announcing the update. Releases created with `GITHUB_TOKEN` do not
trigger another workflow; any future automated release publisher must integrate
the packaging job explicitly or use an approved token that emits release events.

## Rollout and compatibility

Changing the current branch does not retrofit beta9 or older tags. Beta9's own
`hacs.json` has no ZIP switch, so merely adding an asset to beta9 does not switch
its installer. Publish a new prerelease containing both the workflow and config;
no historical tag/backfill is required for clients reading selected-tag metadata.
HACS reloads metadata for the selected ref; Marketplace likewise reads its target
manifest. Cached/wrong-ref metadata must not be treated as proof that an old tag
requires the new asset. Older selected tags keep their original download mode.

**Branch-install limitation:** ZIP mode has no fallback for a missing release
asset in the checked HACS/Marketplace implementations. A branch ref containing
this configuration cannot be installed as a release ZIP. The default `master`
branch is unchanged by this release-branch PR and keeps its existing manifest;
do not propagate the ZIP switch there without deciding whether developer branch
installs should remain supported. Developer installations can still copy the
integration subtree from a checkout. Maintainers must accept this release-only
installer contract before deploying this change; it cannot be conditional on a
tag inside static `hacs.json`.

This reduces the oversized-source-archive/many-file fallback path. It does not
prove that the separately observed HTTP 501 on an empty Python package file is
fixed: that response was not reproducible, and empty files are valid.
