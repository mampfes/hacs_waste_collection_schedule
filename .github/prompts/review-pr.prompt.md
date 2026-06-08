---
description: Maintainer workflow to review a PR in two phases (plan then execute).
---

Review PR #${input:pr_number} using the repository's maintainer process.

Workflow to follow:
1. Run a Phase 1 **pr-reviewer** pass and provide the full PR Review Report.
2. Ask whether to proceed (`yes`, `yes with modifications`, `no`).
3. If approved, execute the approved plan with **pr-executor** semantics.
4. Present the final execution report and any failures verbatim.
5. Include worktree cleanup steps if temporary worktrees were used.
