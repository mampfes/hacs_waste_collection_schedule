---
description: Post-merge cleanup workflow for maintainers.
---

Run the maintainer post-merge cleanup workflow using **repo-cleanup** rules.

Requirements:
- Confirm destructive actions before running them.
- Preserve local-only files (`CLAUDE.local.md`, `.claude/settings.local.json`, `.claude/worktrees/`).
- Provide a final Cleanup Report with branch sync status, deleted branches, removed remotes, and cleaned files.
