Spawn the `release-manager` agent to prepare a new release of `mampfes/hacs_waste_collection_schedule`.

Use the Agent tool with:
- subagent_type: "release-manager"
- description: "Prepare release for hacs_waste_collection_schedule"
- prompt: |
    Prepare the next release.

    Sync master with upstream, gather the PRs merged since the last release, decide the
    semantic version bump, and draft the new CHANGELOG.md section plus matching GitHub
    release notes. Order the sections Removed, Deprecated, Added, Fixed, Other (most
    important to an updating user first). Welcome first-time contributors. Bump the
    `version` in manifest.json.

    Present the full CHANGELOG section, the version number with bump rationale, and the
    release-notes body for approval BEFORE creating any branch, commit, or push. Do not
    create the tag or publish the GitHub release; hand those commands back for the
    maintainer to run after the PR merges.

If `$ARGUMENTS` names a target version (for example `2.29.0`), pass it to the agent as the
intended version and have it confirm the bump still fits the merged changes.

When the agent returns, present its drafts to the user and wait for approval before telling it to proceed.
