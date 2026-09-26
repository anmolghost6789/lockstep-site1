#!/usr/bin/env python3
"""PreToolUse hook: enforce ADLC policy on every tool call.

Blocks (exit 2, reason on stderr, audit event written):
  - direct writes/edits to adlc/.gates/ or adlc/.audit/ (only the ADLC scripts may write there)
  - shell commands that redirect into, delete, or move those folders
  - writes whose content contains secrets
  - MCP calls to servers or tools that are not allow-listed for the current phase
"""
from __future__ import annotations

import fnmatch
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/adlc/scripts"))
from _common import load_json, repo_root  # noqa: E402
from audit_log import append as audit  # noqa: E402
from policy_check import SECRET_PATTERNS  # noqa: E402

PROTECTED = ("adlc/.gates", "adlc/.audit")
MUTATE = re.compile(r"(>>?|\btee\b|\brm\b|\bmv\b|\bcp\b|\bsed\b|\btruncate\b|\bchmod\b|\bln\b)[^;&|]*adlc/\.(gates|audit)")
SCRIPT_OK = re.compile(r"python3?\s+\S*\.claude/skills/adlc/scripts/(adlc_gate|audit_log|state)\.py")


def block(reason: str, phase: str | None, data: dict) -> None:
    try:
        audit("policy.blocked", phase, None, {"reason": reason, **data}, actor="agent")
    finally:
        print(f"ADLC policy: {reason}", file=sys.stderr)
        sys.exit(2)


def main() -> None:
    payload = json.load(sys.stdin)
    tool = payload.get("tool_name", "")
    args = payload.get("tool_input", {}) or {}
    root = repo_root()
    state = load_json(root / "adlc/.state/run_state.json", {}) or {}
    phase = state.get("current_phase")

    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        target = Path(args.get("file_path") or args.get("notebook_path") or "")
        try:
            rel = target.resolve().relative_to(root).as_posix()
        except ValueError:
            block(f"write outside the project is not allowed: {target}", phase, {"tool": tool})
        if rel.startswith(PROTECTED):
            block(f"{rel} is written only by the ADLC gate and audit scripts", phase, {"tool": tool, "path": rel})
        content = args.get("content") or args.get("new_string") or ""
        for edit in args.get("edits", []) or []:
            content += "\n" + edit.get("new_string", "")
        if any(p.search(content) for p in SECRET_PATTERNS):
            block(f"possible secret in content for {rel}", phase, {"tool": tool, "path": rel})

    elif tool == "Bash":
        cmd = args.get("command", "")
        touches = any(p in cmd for p in PROTECTED)
        if MUTATE.search(cmd) or (touches and not SCRIPT_OK.search(cmd)):
            block("shell access to adlc/.gates or adlc/.audit is not allowed; use the ADLC scripts", phase, {"command": cmd[:200]})

    elif tool.startswith("mcp__"):
        _, server, *rest = tool.split("__")
        name = "__".join(rest)
        allow = load_json(root / "config/governance/mcp_allowlist.json")["servers"]
        spec = allow.get(server)
        if not spec:
            block(f"MCP server '{server}' is not allow-listed", phase, {"tool": tool})
        if not any(fnmatch.fnmatch(name, pat) for pat in spec.get("allowed_tools", [])):
            block(f"MCP tool '{name}' on '{server}' is not allow-listed", phase, {"tool": tool})
        phases = spec.get("phases", ["*"])
        if phase and "*" not in phases and phase not in phases:
            block(f"MCP server '{server}' is not allowed during {phase}", phase, {"tool": tool})

    sys.exit(0)


if __name__ == "__main__":
    main()
