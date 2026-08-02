---
name: review-issue
description: Triage a GitHub issue for hacs_waste_collection_schedule and execute only an approved resolution plan. Use when the user asks to review, triage, fix, comment on, label, or close an issue.
---

# Review an issue

1. Extract the issue number. If it is missing or ambiguous, ask for it.
2. Spawn the `issue-triager` custom agent with: `Triage issue #<N> on mampfes/hacs_waste_collection_schedule. Return the complete Phase 1 report and Execution Plan. Do not modify files or GitHub state.`
3. Tell the user triage is running, then wait and present the full report, URL, draft comment, and execution plan.
4. Ask for explicit approval: proceed, proceed with modifications, or stop.
5. Apply requested plan edits and re-present material changes before execution.
6. After approval, spawn the `issue-executor` custom agent with the approved Execution Plan verbatim. Tell it to preserve unrelated user changes.
7. Prefix every approved GitHub-mutating shell command with `WCS_GITHUB_APPROVED=1` so the policy hook can distinguish it from an unapproved post.
8. Present the Execution Report. If a step fails, preserve the workspace and report the exact failure; do not improvise beyond the approved plan.
