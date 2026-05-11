## Step 1 — Spawn the planner (background, isolated worktree)

Use the Agent tool with:
- subagent_type: "pr-reviewer"
- description: "Phase 1 review: PR #$ARGUMENTS"
- isolation: "worktree"
- run_in_background: true
- prompt:
  ```
  Review PR #$ARGUMENTS on mampfes/hacs_waste_collection_schedule. Run Phase 1 now.
  
  Include the full "### Execution Plan" section in your report as specified in your instructions — verbatim bash commands in order, with natural-language descriptions for any code edits that cannot be expressed as a single bash command.
  ```

Notify the user: "Review of PR #$ARGUMENTS is running in the background — the chat is free."

Note the agent ID returned by the Agent tool call in case a SendMessage fallback is needed.

## Step 2 — When the planner notification arrives

Present the full Phase 1 report to the user, including the GitHub URL and the draft review comment.

Ask: "Proceed with the execution plan? (yes / yes with modifications / no / SendMessage fallback)"

## Step 3a — On approval, spawn the executor (separate worktree, background)

Extract the complete "### Execution Plan" section from the Phase 1 report.

Use the Agent tool with:
- subagent_type: "pr-executor"
- description: "Execute approved plan: PR #$ARGUMENTS"
- isolation: "worktree"
- run_in_background: true
- prompt:
  ```
  Execute this pre-approved plan for PR #$ARGUMENTS on mampfes/hacs_waste_collection_schedule:
  
  <PASTE THE EXECUTION PLAN SECTION VERBATIM>
  ```

Notify the user: "Execution of PR #$ARGUMENTS is running in the background."

## Step 3b — SendMessage fallback

If the user requests the SendMessage path (e.g. the execution plan has complex edits better handled by the planner's existing context), use SendMessage to the planner agent with the approved instructions as before.

## Step 4 — When the executor notification arrives

Present the execution report to the user.

If execution failed mid-plan, offer the SendMessage fallback to the original planner agent.

## Step 5 — Worktree cleanup

The Agent tool returns the worktree path when an agent made changes. Collect the paths from both the planner and executor results, then run in the main session:

```bash
git worktree prune
git worktree list
```

For any worktrees still listed (other than the main checkout), remove them:

```bash
git worktree remove --force <path>
```

The planner and executor agent contexts require no explicit close — they expire with the session.
