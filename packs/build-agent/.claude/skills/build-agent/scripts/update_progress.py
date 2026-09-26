#!/usr/bin/env python3
"""
update_progress.py — Derive state/<run_id>/progress.json from session.json.

progress.json is the self-contained source of truth the UI reads to show "what's done,
what's current, and what's recommended next" for a build run. It is derived deterministically
from `session.json` (what each phase recorded) and the canonical phase order in
`workflow_manifest.json` — no hand-authoring, so it never drifts.

This mirrors the requirements agent's progress.json schema (progress-1.0) so both packages
emit the identical shape; the only difference is the source (build reads session.json, which
has no manifest.yaml, and gates generate steps on session.scope_selection).

Schema (progress-1.0):
    { schema_version, run_id, updated_at, selected_outputs,
      current_step, steps: [{id,label,command,status,completed_at}], next: {command,label,why} }

Step status: "done" | "pending" | "skipped" (family not in scope / phase not applicable).

Usage:
    python .claude/skills/build-agent/scripts/update_progress.py <run_id>
    python .claude/skills/build-agent/scripts/update_progress.py <run_id> --completed ddl --at 2026-06-01T12:00:00Z

Exit 0 when the run dir exists; exit 1 if state/<run_id>/ is missing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PRE_STEPS = [
    {"id": "start", "command": "/start-build-run", "label": "Start Build Run"},
    {"id": "analyze", "command": "/analyze-inputs", "label": "Analyze Inputs"},
    {"id": "plan", "command": "/plan-build", "label": "Plan Build"},
]
EVALUATE_STEP = {"id": "evaluate", "command": "/evaluate-build", "label": "Evaluate Build"}
PUBLISH_STEP = {"id": "publish", "command": "/publish-build-summary", "label": "Publish Build Summary"}

WHY = {
    "analyze": "Analyze and normalize the inputs before planning.",
    "plan": "Plan dependency waves and per-table plans before generating.",
    "evaluate": "All selected artifacts are generated — evaluate before publishing.",
    "publish": "Publish the build summary to Jira.",
}

# session.generation_summary flags that mark a family complete (any → done).
GEN_FLAGS = {
    "ddl": ["ddl_complete"],
    "dml": ["dml_complete"],
    "dq": ["dq_complete"],
    "pipeline": ["pipeline_complete"],
    "tests": ["tests_data_complete", "tests_pipeline_complete", "tests_complete"],
}


def package_root() -> Path:
    here = Path(__file__).resolve()
    candidate = here.parents[4]
    if (candidate / "state").is_dir() or (candidate / "outputs").is_dir():
        return candidate
    cwd = Path.cwd()
    for path in (cwd, *cwd.parents):
        if (path / "state").is_dir() and (path / "outputs").is_dir():
            return path
    return candidate


def workflow_manifest() -> dict:
    path = Path(__file__).resolve().parents[1] / "workflow_manifest.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_session(run_src: Path) -> dict:
    path = run_src / "session.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def generate_steps(wf: dict) -> list[dict]:
    """Ordered Generate-<family> steps from workflow_manifest outputs."""
    outputs = {str(o.get("id")): o for o in (wf.get("outputs") or [])}
    order = wf.get("generationOrder") or list(outputs.keys())
    steps = []
    for code in order:
        out = outputs.get(code)
        if not out:
            continue
        steps.append({
            "id": str(out.get("scopeKey") or code).lower(),
            "scope_key": str(out.get("scopeKey") or code).lower(),
            "command": out.get("command") or f"/generate-{str(code).lower()}",
            "label": f"Generate {out.get('label') or code}",
        })
    return steps


def has_jira(session: dict) -> bool:
    for key in ("jira", "jira_context", "jira_seeded"):
        if session.get(key):
            return True
    return False


def is_done(step: dict, session: dict) -> bool:
    sid = step["id"]
    if sid == "start":
        return bool(session.get("scope_selection"))
    if sid == "analyze":
        return bool(session.get("analysis_summary"))
    if sid == "plan":
        return bool(session.get("planning_summary"))
    if sid == "evaluate":
        return bool(session.get("evaluation_summary"))
    if sid == "publish":
        return bool(session.get("build_summary_published") or session.get("published_at"))
    flags = GEN_FLAGS.get(step.get("scope_key") or sid, [])
    gen = session.get("generation_summary") or {}
    return any(bool(gen.get(flag)) for flag in flags)


def build_progress(run_id, session, wf, completed, at) -> dict:
    scope = session.get("scope_selection") or {}
    has_scope = bool(scope)
    jira = has_jira(session)

    canonical = [*PRE_STEPS, *generate_steps(wf), EVALUATE_STEP, PUBLISH_STEP]
    selected_outputs = []
    steps: list[dict] = []
    for step in canonical:
        sk = step.get("scope_key")
        skipped = False
        if sk:  # a generate family — gated by scope_selection
            if has_scope and not scope.get(sk):
                skipped = True
            elif scope.get(sk):
                selected_outputs.append(step["id"].upper())
        if step["id"] == "publish" and not jira:
            skipped = True
        if skipped:
            status = "skipped"
        elif is_done(step, session):
            status = "done"
        else:
            status = "pending"
        steps.append({
            "id": step["id"],
            "label": step["label"],
            "command": step["command"],
            "status": status,
            "completed_at": at if (step["id"] == completed and status == "done") else None,
        })

    done_ids = [s["id"] for s in steps if s["status"] == "done"]
    current_step = completed if (completed and completed in {s["id"] for s in steps}) else (done_ids[-1] if done_ids else None)

    next_step = next((s for s in steps if s["status"] == "pending"), None)
    nxt = None
    if next_step:
        why = WHY.get(next_step["id"]) or f"{next_step['label']} is the next step in the build."
        nxt = {"command": next_step["command"], "label": next_step["label"], "why": why}

    return {
        "schema_version": "progress-1.0",
        "run_id": run_id,
        "updated_at": at,
        "selected_outputs": selected_outputs,
        "current_step": current_step,
        "steps": steps,
        "next": nxt,
    }


def write_progress(root: Path, run_id: str, completed: str | None = None, at: str | None = None) -> Path | None:
    """Derive and write state/<run_id>/progress.json. Returns the path, or None if the run dir is missing."""
    run_src = root / "state" / run_id
    if not run_src.is_dir():
        return None
    payload = build_progress(run_id, load_session(run_src), workflow_manifest(), completed, at)
    out = run_src / "progress.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def seed_progress(workspace: Path) -> Path:
    """Write the baseline progress.json to the workspace root.

    Called by the playground backend at run creation, before any state/<run_id>/
    exists. With an empty session every step is 'pending' and `next` points at the
    first step (/start-build-run), so the UI shows the real plan from the first
    render. The in-run write_progress() later supersedes this from the state dir.
    """
    payload = build_progress(workspace.name, {}, workflow_manifest(), None, None)
    out = workspace / "progress.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id", nargs="?", help="e.g. run_id_20260514T115958Z")
    parser.add_argument("--completed", help="step id that just finished (pins current_step)")
    parser.add_argument("--at", help="ISO timestamp for the completed step's completed_at")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Write the baseline progress.json to the current working directory (run root).",
    )
    args = parser.parse_args()

    if args.seed:
        out = seed_progress(Path.cwd())
        print(f"Wrote {out} (seed baseline)")
        return 0

    if not args.run_id:
        print("ERROR: run_id is required unless --seed is given", file=sys.stderr)
        return 1

    out = write_progress(package_root(), args.run_id, args.completed, args.at)
    if out is None:
        print(f"ERROR: state/{args.run_id}/ not found", file=sys.stderr)
        return 1
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
