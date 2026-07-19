---
name: review-pr
description: Review a pull request for hacs_waste_collection_schedule and execute only approved fixes or review actions. Use when the user asks to inspect, fix, approve, or request changes on a PR.
---

# Review a pull request

1. Extract the PR number. If it is missing or ambiguous, ask for it.
2. Spawn the `pr-reviewer` custom agent with: `Review PR #<N> on mampfes/hacs_waste_collection_schedule. Return the complete Phase 1 report and Execution Plan. Do not modify files, checkout branches, or change GitHub state.`
3. Tell the user review is running, then wait and present the full report, URL, draft review, and execution plan.
4. Ask for explicit approval: proceed, proceed with modifications, or stop.
5. Apply requested plan edits and re-present material changes before execution.
6. After approval, spawn the `pr-executor` custom agent with the approved Execution Plan verbatim. Tell it to preserve unrelated local changes and stop if checkout would overwrite them.
7. Prefix every approved GitHub-mutating shell command with `WCS_GITHUB_APPROVED=1` so the policy hook can distinguish it from an unapproved post.
8. Present the Execution Report. If a step fails, preserve the workspace and report the exact failure; do not improvise beyond the approved plan.
