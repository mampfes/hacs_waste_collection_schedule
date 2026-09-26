"""PreToolUse guard for Bash commands (wired in .claude/settings.json).

Claude Code passes the tool call as JSON on stdin. Two checks:

- update_docu_links.py is blocked outright: CI runs it post-merge, and a manual
  run in a PR branch corrupts the generated files.
- Commands that post or modify content on GitHub (comments, closes, reviews,
  discussion replies) require an explicit confirmation from the user, so a
  draft is never posted unseen.
"""

import json
import sys

POSTING = (
    "gh issue comment",
    "gh issue close",
    "gh issue reopen",
    "gh pr review",
    "gh pr comment",
    "gh discussion",
    "addDiscussionComment",
)


def main() -> None:
    try:
        command = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    except (ValueError, AttributeError):
        return

    if "update_docu_links.py" in command:
        print(
            "update_docu_links.py must never be run manually: the Update "
            "Documentation CI workflow runs it after every push to master, and "
            "a manual run in a PR branch corrupts the generated files.",
            file=sys.stderr,
        )
        sys.exit(2)

    if any(p in command for p in POSTING) or (
        "gh api" in command and "/reviews" in command
    ):
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": (
                        "This posts or modifies content on GitHub. Confirm the "
                        "exact text was shown to and approved by the user."
                    ),
                }
            },
            sys.stdout,
        )


if __name__ == "__main__":
    main()
