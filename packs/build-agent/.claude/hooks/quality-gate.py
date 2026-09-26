#!/usr/bin/env python3
"""
Hook: quality-gate
Event: PreToolUse (matcher: Write)
Purpose: Block obvious template residue from being written into generated build
         artifacts (DDL, DML, DQ, pipeline YAML, tests).

Lightweight — full quality review lives in references/quality_standards.md and
the build-evaluator subagent. This hook only catches the most embarrassing
template leakage.
"""

import json
import os
import re
import sys

BLOCK_PATTERNS = [
    (r"<!--", "HTML template comments remain"),
    (r"\[PLACEHOLDER\]", "placeholder marker remains"),
    (r"<TABLE_NAME>|<COLUMN_NAME>|<SOURCE_TABLE>|<TARGET_TABLE>|<RUN_ID>", "template token remains"),
    (r"\bFIXME\b", "FIXME marker remains in generated artifact"),
]

GENERATED_FAMILIES = ("/generated/ddl/", "/generated/dml/", "/generated/dq/",
                      "/generated/pipeline/", "/generated/tests_data/",
                      "/generated/tests_pipeline/")


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    if hook_input.get("tool_name") != "Write":
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "") or ""

    # Only inspect generated build artifacts in state/ or outputs/.
    if not any(fam in file_path for fam in GENERATED_FAMILIES):
        sys.exit(0)

    basename = os.path.basename(file_path)
    if basename.startswith(".") or basename in {"INDEX.md", "README.md"}:
        sys.exit(0)

    findings = []
    for pattern, label in BLOCK_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(label)

    if findings:
        reason = (
            f"Blocked write to {basename}: "
            + "; ".join(findings)
            + ". Fix template residue before promoting the artifact."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "additionalContext": reason,
            }
        }))
        sys.stderr.write(reason + "\n")
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
