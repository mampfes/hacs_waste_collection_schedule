"""Block unsafe repository commands before Codex executes them."""

from __future__ import annotations

import json
import re
import sys
from typing import Any

APPROVAL_MARKER = "WCS_GITHUB_APPROVED=1"

GITHUB_MUTATIONS = (
    re.compile(r"\bgh\s+issue\s+(?:comment|close|reopen|edit)\b"),
    re.compile(r"\bgh\s+pr\s+(?:review|comment|create|edit|close|reopen|merge)\b"),
    re.compile(r"\bgh\s+discussion\b"),
    re.compile(r"\bgh\s+release\s+(?:create|edit|delete|upload)\b"),
    re.compile(r"\baddDiscussionComment\b"),
    re.compile(r"\bgh\s+api\b[^\n]*(?:/reviews\b|\b-X\s*(?:POST|PATCH|PUT|DELETE)\b)"),
)


def _command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input", {})
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "")
        if isinstance(command, str):
            return command
    return ""


def _deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    json.dump(response, sys.stdout)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0

    if not isinstance(payload, dict):
        return 0

    command = _command(payload)
    if not command:
        return 0

    if "update_docu_links.py" in command:
        _deny(
            "update_docu_links.py must never run manually. The post-merge "
            "Update Documentation workflow regenerates these files."
        )
        return 0

    if any(pattern.search(command) for pattern in GITHUB_MUTATIONS):
        if APPROVAL_MARKER not in command:
            _deny(
                "This command modifies GitHub. Present the exact draft to the "
                "user and obtain explicit approval first. After approval, rerun "
                f"the command with {APPROVAL_MARKER}."
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
