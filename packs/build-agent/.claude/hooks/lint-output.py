#!/usr/bin/env python3
"""
Hook: lint-output
Event: PostToolUse (matcher: Write|Edit)
Purpose: Lightweight reminder after build artifacts are written. Catches
         template residue and unresolved markers in generated SQL/YAML/MD.
         Never blocks — only nudges Claude.
"""

import json
import os
import re
import sys

PLACEHOLDER_PATTERNS = [
    r"<!--",
    r"\bTODO\b",
    r"\bTBD\b",
    r"\bFIXME\b",
    r"<TABLE_NAME>|<COLUMN_NAME>|<SOURCE_TABLE>|<TARGET_TABLE>|<RUN_ID>",
    r"\[PLACEHOLDER\]",
    r"\[TBD\]",
    r"\[TODO\]",
]

INTERESTING_EXTENSIONS = (".sql", ".py", ".yml", ".yaml", ".json", ".md")


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
    if not file_path.endswith(INTERESTING_EXTENSIONS):
        sys.exit(0)
    if "/runs/" not in file_path and "/outputs/" not in file_path:
        sys.exit(0)
    if "/generated/" not in file_path:
        sys.exit(0)

    basename = os.path.basename(file_path)
    if basename.startswith(".") or basename in {"README.md", "phase_handoff.json"}:
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
            f"[lint-output] {basename} may contain template residue or unresolved markers: "
            + ", ".join(flags[:5])
            + ". Review references/quality_standards.md before promoting."
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
