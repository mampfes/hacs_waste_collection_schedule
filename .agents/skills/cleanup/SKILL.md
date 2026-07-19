---
name: cleanup
description: Clean the local hacs_waste_collection_schedule repository after a pull request merges. Use when a maintainer asks to clean merged branches, resync master, prune remotes, or prepare the checkout for the next ticket.
---

# Clean the repository

1. Spawn the `repo-cleanup` custom agent with this task: `Run the full post-merge cleanup workflow. Preserve all personal and tool-local files, confirm every destructive action, and report the final state.`
2. Keep all cleanup work in the main checkout. Do not create an agent worktree.
3. Preserve `CLAUDE.local.md`, `.claude/settings.local.json`, `.claude/worktrees/`, `.codex/`, `.agents/skills/`, and any `*.local.*` path unless the user explicitly targets it.
4. Require the agent to confirm the merged PR, uncommitted-change handling, branch deletions, force deletions, remote deletions, and `origin/master` overwrite separately as its instructions require.
5. Present the agent's cleanup report to the user. Surface any skipped or blocked step; do not imply the repository is clean unless the final checks prove it.
