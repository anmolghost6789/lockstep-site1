#!/usr/bin/env python3
"""
Hook: verify-completeness
Event: Stop
Purpose: Before Claude finishes a turn, verify that every selected build
         scope (DDL/DML/DQ/Pipeline/Tests) marked complete in session.json
         actually has artifacts on disk. Exit 2 forces Claude to continue.

Dual-mode detection:
- Playground mode: agent cwd IS the run directory (session.json at cwd root)
- Standalone mode: agent cwd is skill package root (runs/run_id_*/ subdirectories)
"""

import sys
import json
import os
from pathlib import Path


# Each scope item maps to the relative folder its artifacts land in,
# under state/<run_id>/generated/<family>/.
SCOPE_FAMILY = {
    "DDL": "ddl",
    "DML": "dml",
    "DQ": "dq",
    "PIPELINE": "pipeline",
    "TESTS": "tests_data",   # primary; tests_pipeline is checked too if TESTS is selected
}

GENERATION_PHASES = [
    "generation", "generating", "generate",
    "ddl_generated", "dml_generated", "dq_generated",
    "pipeline_generated", "tests_generated",
    "evaluate", "evaluation", "all_generated", "evaluation_complete",
]


def find_run_root(project_root: Path):
    """Return (run_root, session_file) for the active run, or (None, None)."""
    # Playground mode — cwd IS the run directory
    session_file = project_root / "session.json"
    if session_file.exists():
        return project_root, session_file

    # Standalone mode — cwd is the skill package root
    runs_dir = project_root / "runs"
    if not runs_dir.exists():
        return None, None

    run_dirs = sorted(runs_dir.glob("run_id_*"), reverse=True)
    if not run_dirs:
        return None, None

    latest_run = run_dirs[0]
    session_file = latest_run / "session.json"
    return latest_run, session_file


def _has_artifacts(run_root: Path, family: str) -> bool:
    """True if at least one non-empty file exists under state/<run>/generated/<family>/."""
    candidates = [
        run_root / "state" / "generated" / family,
        run_root / "generated" / family,
    ]
    for d in candidates:
        if d.exists() and any(p.is_file() and p.stat().st_size > 0 for p in d.rglob("*")):
            return True
    return False


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    project_root = Path(os.getcwd())
    run_root, session_file = find_run_root(project_root)

    if run_root is None or session_file is None or not session_file.exists():
        sys.exit(0)

    try:
        with open(session_file) as f:
            session = json.load(f)
    except Exception:
        sys.exit(0)

    active_phase = (session.get("active_phase") or "").lower()
    generation_summary = session.get("generation_summary", {}) or {}

    is_generation_phase = any(gp in active_phase for gp in GENERATION_PHASES)
    has_any_generated = len(generation_summary) > 0

    if not is_generation_phase and not has_any_generated:
        sys.exit(0)

    selected = session.get("selected_scope", []) or session.get("selected_outputs", [])
    if not selected:
        sys.exit(0)

    missing = []
    for scope_id in selected:
        sid = scope_id.upper()
        gen_info = generation_summary.get(sid) or generation_summary.get(scope_id) or {}
        if not (isinstance(gen_info, dict) and gen_info.get("status") == "complete"):
            continue
        family = SCOPE_FAMILY.get(sid)
        if family is None:
            continue
        if not _has_artifacts(run_root, family):
            missing.append(sid)
        # If TESTS, also require tests_pipeline to have content
        if sid == "TESTS" and not _has_artifacts(run_root, "tests_pipeline"):
            missing.append("TESTS:pipeline")

    if missing:
        reason = (
            f"Completeness check: build families marked complete but artifacts missing: "
            f"{', '.join(missing)}. "
            f"Re-generate before finishing."
        )
        print(json.dumps({
            "decision": "block",
            "reason": reason,
        }))
        sys.stderr.write(reason + "\n")
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
