#!/usr/bin/env python3
"""
Hook: lint-output
Event: PostToolUse (matcher: Write|Edit)
Purpose: Lightweight reminder after markdown deliverables are written.

It gives Claude a small checklist nudge and never blocks.
"""

import json
import os
import re
import sys

# Patterns indicating template residue or unresolved drafts.
# IMPORTANT: keep these narrow. A blanket `<[^>]+>` matches legitimate angle-bracket
# placeholders in EARS examples ("the <system> shall ..."), URS verification
# intents, and template citations — producing constant false-positive warnings.
# Match only obvious template tokens (uppercase or CamelCase inside angle brackets
# with no spaces, or explicit placeholder words).
PLACEHOLDER_PATTERNS = [
    r"<!--",                                                # HTML comments
    r"\bTODO\b",                                            # word-boundary TODO
    r"\bTBD\b",                                             # word-boundary TBD
    r"<[A-Z][A-Z0-9_]+>",                                   # <UPPERCASE_TOKEN>
    r"<[A-Z][A-Za-z0-9]* [A-Z][A-Za-z0-9]*>",                # <Capability Name>
    r"\[PLACEHOLDER\]",
    r"\[TBD\]",
    r"\[TODO\]",
]


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path.endswith(".md"):
        sys.exit(0)
    if "/outputs/" not in file_path:
        sys.exit(0)

    basename = os.path.basename(file_path)
    if basename.startswith(".") or basename == "README.md":
        sys.exit(0)

    content = ""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(100000)
        except Exception:
            content = ""

    flags = []
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            flags.append(pattern)

    if flags:
        context = (
            f"[lint-output] {basename} may contain template residue or unresolved placeholders: "
            + ", ".join(flags[:5])
            + ". Review quality_checks.md before syncing final outputs."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": context,
            }
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()
