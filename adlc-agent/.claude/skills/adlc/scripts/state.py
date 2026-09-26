#!/usr/bin/env python3
"""Run-state bookkeeping. Writes adlc/.state/run_state.json and derives root progress.json.

  state.py start    --phase architect-design
  state.py complete --phase architect-design
  state.py wait     --phase architect-design --action gate_approval
  state.py cancel   --reason "..."
  state.py show
  state.py refresh                      re-derive progress.json after an external change

progress.json is a projection for the VS Code extension; never edit it by hand.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid

from _common import load_json, manifest, now, repo_root, write_json
from audit_log import append as audit


def _state(root):
    return load_json(root / "adlc/.state/run_state.json") or {
        "schema_version": "adlc-state-1.0",
        "run_id": f"adlc-{uuid.uuid4().hex[:8]}",
        "created_at": now(),
        "run_status": "not_started",
        "current_phase": None,
        "awaiting_user_action": None,
        "phases": {},
    }


def _save(root, state):
    state["updated_at"] = now()
    write_json(root / "adlc/.state/run_state.json", state)
    _project(root, state)


def _project(root, state):
    phases = manifest(root)["phases"]
    steps = []
    for p in phases:
        ps = state["phases"].get(p["id"], {})
        gate = load_json(root / "adlc/.gates" / f"{p['gate']}.json") or {}
        steps.append({
            "id": p["id"],
            "label": f"{p['number']} {p['label']}",
            "status": ps.get("status", "pending"),
            "gate": {"id": p["gate"], "status": gate.get("status", "not_requested")},
            "artifact": p["artifact"],
            "completed_at": ps.get("completed_at"),
        })
    nxt = None
    for p, s in zip(phases, steps):
        if s["gate"]["status"] == "pending":
            nxt = {"command": f"/approve-gate {p['gate']}", "why": f"{p['gate']} needs a named approver before the next phase."}
            break
        if s["status"] != "done":
            nxt = {"command": f"/{p['id']}", "why": f"Run {p['label']}."}
            break
    write_json(root / "progress.json", {
        "schema_version": "progress-1.0",
        "run_id": state["run_id"],
        "updated_at": state["updated_at"],
        "run_status": state["run_status"],
        "current_step": state["current_phase"],
        "awaiting_user_action": state["awaiting_user_action"],
        "steps": steps,
        "next": nxt,
    })


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["start", "complete", "wait", "cancel", "show", "refresh"])
    ap.add_argument("--phase")
    ap.add_argument("--action")
    ap.add_argument("--reason", default="")
    args = ap.parse_args()
    root = repo_root()
    state = _state(root)

    if args.cmd == "refresh":
        _save(root, state)
        print("progress.json refreshed.")
        return 0
    if args.cmd == "show":
        print(json.dumps(state, indent=2))
        return 0
    if args.cmd == "cancel":
        state["run_status"] = "cancelled"
        state["awaiting_user_action"] = None
        _save(root, state)
        audit("run.cancelled", state.get("current_phase"), None, {"reason": args.reason})
        print("Run cancelled. Artifacts, gates and audit log are preserved.")
        return 0
    if not args.phase:
        ap.error("--phase is required")
    ps = state["phases"].setdefault(args.phase, {})
    if args.cmd == "start":
        state.update(run_status="in_progress", current_phase=args.phase, awaiting_user_action=None)
        ps.update(status="running", started_at=now())
        audit("phase.started", args.phase, None, {"run_id": state["run_id"]})
    elif args.cmd == "complete":
        state.update(run_status="waiting_for_user", awaiting_user_action="gate_approval")
        ps.update(status="done", completed_at=now())
        audit("phase.completed", args.phase, None, {"run_id": state["run_id"]})
    elif args.cmd == "wait":
        state.update(run_status="waiting_for_user", awaiting_user_action=args.action or "clarification")
    _save(root, state)
    print(f"{args.phase}: {ps['status']} (run {state['run_status']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
