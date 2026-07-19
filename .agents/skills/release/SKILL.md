---
name: release
description: Prepare a guarded release of hacs_waste_collection_schedule. Use when a maintainer asks for the next release, a target version, changelog drafting, a manifest bump, or a release pull request.
---

# Prepare a release

1. Parse an optional target version from the user's request.
2. Spawn the `release-manager` custom agent. Ask it to inspect merged PRs, determine or validate the semantic version, and return the complete CHANGELOG section, manifest change, and GitHub release-notes body.
3. Do not let the agent create a branch, commit, push, tag, release, or PR during the draft phase.
4. Present every draft verbatim with the bump rationale and ask the user for explicit approval.
5. If the user requests changes, send them to the same agent and re-present the revised drafts.
6. Only after explicit approval, send the agent: `Proceed with the approved release PR exactly as drafted. Prefix any approved mutating gh command with WCS_GITHUB_APPROVED=1.`
7. Present the release PR URL and exact post-merge tag/release commands. Never create the tag or publish the GitHub release.
