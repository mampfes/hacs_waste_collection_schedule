---
description: Maintainer workflow to triage and resolve an issue in two phases (plan then execute).
---

Triage issue #${input:issue_number} using the repository's maintainer process.

Workflow to follow:
1. Run a Phase 1 **issue-triager** pass and provide the full Issue Triage Report.
2. Ask whether to proceed (`yes`, `yes with modifications`, `no`).
3. If approved, execute the approved plan with **issue-executor** semantics.
4. Present the final execution report and any failures verbatim.
5. Include worktree cleanup steps if temporary worktrees were used.
