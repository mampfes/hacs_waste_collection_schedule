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

Present the full Phase 1 report to the user, including the GitHub URL, the reviewed SHA and the draft review comment.

Ask: "Proceed with the execution plan? (yes / yes with modifications / no / SendMessage fallback)"

## Step 3a — On approval, spawn the executor (separate worktree, background)

Approval covers the reviewed SHA only. Before spawning, compare it with the current head:

```bash
gh pr view $ARGUMENTS --repo mampfes/hacs_waste_collection_schedule --json headRefOid --jq .headRefOid
```

If the head has moved, do not spawn the executor. List what changed since the reviewed SHA and tell the user:

- Only a merge of the base branch that leaves the reviewed files unchanged: update the affected findings and any SHA or CI statement in the text, then ask for approval of the changed text.
- Anything else: go back to Step 1, naming the reviewed SHA and the earlier findings so the planner can classify each one as fixed, still present or changed.

Then extract the complete "### Execution Plan" section from the Phase 1 report.

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

If execution failed mid-plan, offer the SendMessage fallback to the original planner agent. If a posting command was denied, report that: the hook in `.claude/hooks/guard_bash.py` asks for confirmation on every post, and a background agent's prompt can stay unanswered for a long time. Do not re-run the command from the main session. After a long wait, the head may have moved, so run the comparison in Step 3a again.

If the plan posted something, confirm it on GitHub from the main session rather than relying on the executor's report.

## Step 5 — Worktree cleanup

The Agent tool returns the worktree path when an agent made changes. Collect the paths from the planner and executor results of this run, then run in the main session:

```bash
git worktree prune
git worktree list
```

Remove only those worktrees, and only after checking that `git -C <path> status --short` is empty or that the changes belong to this run. Other sessions keep worktrees here too, sometimes with uncommitted work, so never remove a worktree this run did not create:

```bash
git worktree remove --force <path>
```

The planner and executor agent contexts require no explicit close — they expire with the session.
