"""PreToolUse guard for Bash commands (wired in .claude/settings.json).

Claude Code passes the tool call as JSON on stdin. Two checks:

- update_docu_links.py is blocked outright: CI runs it post-merge, and a manual
  run in a PR branch corrupts the generated files.
- Commands that post or modify content on GitHub (comments, closes, reviews,
  discussion replies, any writing `gh api` call) require an explicit
  confirmation from the user, so a draft is never posted unseen. Reads are
  not gated: a reviewer fetches `pulls/<n>/reviews` on every PR.
"""

import json
import re
import shlex
import sys

POSTING = (
    "gh issue comment",
    "gh issue close",
    "gh issue reopen",
    "gh pr review",
    "gh pr comment",
    "addDiscussionComment",
)

# `gh api` sends a POST as soon as a field or body is given.
FIELD_FLAGS = ("-f", "-F", "--field", "--raw-field", "--input")
METHOD_FLAGS = ("-X", "--method")


def _segments(command: str) -> list[list[str]]:
    """Split a command line into simple commands, honouring quotes (a `|`
    inside `--jq '... | ...'` is not a pipe)."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        tokens = re.split(r"\s+", command)
    segments: list[list[str]] = [[]]
    for tok in tokens:
        if tok and set(tok) <= set(";&|\n"):
            segments.append([])
        elif tok:
            segments[-1].append(tok)
    return segments


def _is_write(tokens: list[str]) -> bool:
    for i, tok in enumerate(tokens):
        flag, _, value = tok.partition("=")
        if flag in METHOD_FLAGS:
            method = value or (tokens[i + 1] if i + 1 < len(tokens) else "")
            if method.upper() != "GET":
                return True
        elif tok.startswith("-X") and len(tok) > 2:
            if tok[2:].upper() != "GET":
                return True
        elif flag in FIELD_FLAGS or (
            tok[:2] in ("-f", "-F") and len(tok) > 2 and not tok.startswith("--")
        ):
            return True
    return False


def _gh_api_writes(command: str) -> bool:
    for segment in _segments(command):
        starts = [
            i
            for i in range(len(segment) - 1)
            if segment[i] == "gh" and segment[i + 1] == "api"
        ]
        if not starts:
            continue
        tokens = segment[starts[0] :]
        if "graphql" in tokens[2:]:
            # Queries also pass `-f query=...`; only a mutation writes.
            if any("mutation" in t for t in tokens):
                return True
        elif _is_write(tokens):
            return True
    return False


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

    if any(p in command for p in POSTING) or _gh_api_writes(command):
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
