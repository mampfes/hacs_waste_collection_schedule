---
name: "source-command-cleanup"
description: "Migrated source command `cleanup`"
---

# source-command-cleanup

Use this skill when the user asks to run the migrated source command `cleanup`.

## Command Template

Spawn the `repo-cleanup` agent to clean up the local repository after a PR has been merged.

Use the Agent tool with:
- subagent_type: "repo-cleanup"
- description: "Post-merge cleanup for hacs_waste_collection_schedule"
- prompt: |
    Run the full post-merge cleanup workflow.

    Preserve these local-only paths if they exist (do NOT delete or discard them):
    - `Codex.local.md` (root) — personal maintainer overrides on top of the tracked `AGENTS.md`
    - `.Codex/settings.local.json` — personal Codex permissions and hooks
    - `.Codex/worktrees/` — Codex internal state

    The tracked `AGENTS.md` and `.Codex/agents/` / `.Codex/commands/` directories are
    part of the repo and will be preserved automatically by git — no special handling needed.

    Confirm uncommitted changes with the user before discarding. Confirm branch deletions
    before running them. Report the final state.

When the agent returns, present the cleanup summary to the user.
