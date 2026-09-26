#!/usr/bin/env python3
"""PostToolUse hook: record every change to a lifecycle artifact in the audit log."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/adlc/scripts"))
from _common import load_json, repo_root, sha256_file  # noqa: E402
from audit_log import append as audit  # noqa: E402


def main() -> None:
    payload = json.load(sys.stdin)
    if payload.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)
    root = repo_root()
    target = Path((payload.get("tool_input") or {}).get("file_path", ""))
    try:
        rel = target.resolve().relative_to(root).as_posix()
    except ValueError:
        sys.exit(0)
    if rel.startswith("adlc/") and not rel.startswith("adlc/."):
        state = load_json(root / "adlc/.state/run_state.json", {}) or {}
        digest = sha256_file(target) if target.exists() else None
        audit("artifact.modified", state.get("current_phase"), None, {"path": rel, "sha256": digest}, actor="agent")
    sys.exit(0)


if __name__ == "__main__":
    main()
