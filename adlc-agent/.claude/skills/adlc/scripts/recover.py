#!/usr/bin/env python3
"""ADLC recovery. Finds what is wrong with a run and says the next safe action; routes changes.

  recover.py diagnose                          interrupted phases, invalid artifacts, gate drift, audit chain
  recover.py change --type <type> --summary "…" [--ids FR-002,NFR-003]
                                               route a change to the earliest phase that owns it and
                                               mark every later phase stale, so their gates must be re-requested
  recover.py changes                           list recorded changes

Change types: wording, requirement, design, defect, eval_setup, release, production
(see utilities/change-impact-routing.md). Standard library only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path

from _common import load_json, manifest, now, repo_root, write_json
from audit_log import append as audit

ROUTES = {
    "wording": ("same", "Re-request that phase's gate only."),
    "requirement": ("discover-define", "Requirements and thresholds are owned by phase 01."),
    "design": ("architect-design", "Units, agents, models, tools and RAG design are owned by phase 02."),
    "defect": ("build-orchestrate", "Fix in a new bolt; evaluation re-runs afterwards."),
    "eval_setup": ("evaluate-validate", "Dataset, case count or metric definition; thresholds belong to phase 01."),
    "release": ("release-operate", "Rollout, flags, runbook or rollback triggers."),
    "production": ("observe-evolve", "Production learning becomes a backlog item and the next intent."),
}
SCRIPTS = Path(__file__).resolve().parent


def run_script(root: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(SCRIPTS / args[0]), *args[1:]], capture_output=True, text=True, cwd=root)
    return p.returncode, (p.stdout + p.stderr).strip()


def gate_mode(root: Path) -> str:
    cfg = load_json(root / "config/project_config.json", {}) or {}
    gm = cfg.get("gate_mode", {})
    return gm.get("value", "github") if isinstance(gm, dict) else str(gm)


def diagnose(root: Path) -> list[dict]:
    findings: list[dict] = []
    phases = manifest(root)["phases"]
    state = load_json(root / "adlc/.state/run_state.json")
    if not state:
        return [{"level": "info", "what": "No run yet.", "do": "/discover-define"}]

    running = [p for p, v in state.get("phases", {}).items() if v.get("status") == "running"]
    for p in running:
        findings.append({"level": "warn", "what": f"{p} was interrupted (still marked running).", "do": f"Re-run /{p}; it resumes from completed work."})
    for p, v in state.get("phases", {}).items():
        if v.get("status") == "stale":
            findings.append({"level": "warn", "what": f"{p} is stale after a change upstream.", "do": f"Re-run /{p} and request its gate again."})

    mode = gate_mode(root)
    for ph in phases:
        artifact = root / ph["artifact"]
        pstate = state.get("phases", {}).get(ph["id"], {})
        if pstate.get("status") in ("done", "stale") and not artifact.exists():
            findings.append({"level": "error", "what": f"{ph['artifact']} is missing although {ph['id']} completed.", "do": f"Re-run /{ph['id']}."})
            continue
        if not artifact.exists():
            continue
        code, out = run_script(root, "validate_artifact.py", "--phase", ph["id"])
        if code != 0:
            findings.append({"level": "error", "what": f"{ph['artifact']} fails validation: {out.splitlines()[1].strip(' -') if len(out.splitlines()) > 1 else out}", "do": f"Fix it in /{ph['id']}, then request {ph['gate']} again."})
        if mode == "local":
            code, out = run_script(root, "adlc_gate.py", "check", "--gate", ph["gate"])
            if code == 4:
                findings.append({"level": "error", "what": f"{ph['artifact']} changed after {ph['gate']} was approved.", "do": f"Re-run /{ph['id']} and request {ph['gate']} again; later gates must follow."})
            elif code == 5:
                findings.append({"level": "warn", "what": f"{ph['gate']} was rejected.", "do": f"Address the reviewer's comments in /{ph['id']}."})
            elif code == 6:
                findings.append({"level": "warn", "what": f"The {ph['gate']} waiver has expired.", "do": "Request the gate or a new waiver."})

    if (root / "adlc/.audit/audit.jsonl").exists():
        code, out = run_script(root, "audit_log.py", "verify")
        if code != 0:
            findings.insert(0, {"level": "critical", "what": out, "do": "Stop gate decisions and contact the platform team before continuing."})

    for ev in ("license_scan", "sbom_present"):
        p = root / f"adlc/.state/evidence/{ev}.json"
        if p.exists() and (load_json(p) or {}).get("passed") is False:
            findings.append({"level": "warn", "what": f"CI evidence {ev} reports a failure.", "do": "Fix the findings in CI; the gate stays blocked until evidence passes."})

    if not findings:
        progress = load_json(root / "progress.json", {}) or {}
        nxt = progress.get("next") or {}
        findings.append({"level": "ok", "what": "The run is consistent.", "do": nxt.get("command", "/status")})
    return findings


def cmd_diagnose(_args) -> int:
    root = repo_root()
    order = {"critical": 0, "error": 1, "warn": 2, "info": 3, "ok": 4}
    f = sorted(diagnose(root), key=lambda x: order[x["level"]])
    write_json(root / "adlc/.state/diagnosis.json", {"checked_at": now(), "findings": f})
    for x in f:
        print(f"[{x['level'].upper()}] {x['what']}\n        → {x['do']}")
    return 1 if any(x["level"] in ("critical", "error") for x in f) else 0


def cmd_change(args) -> int:
    root = repo_root()
    if args.type not in ROUTES:
        print(f"Unknown change type. Use one of: {', '.join(ROUTES)}")
        return 2
    phases = [p["id"] for p in manifest(root)["phases"]]
    state = load_json(root / "adlc/.state/run_state.json") or {"phases": {}}
    target, why = ROUTES[args.type]
    if target == "same":
        target = args.phase or state.get("current_phase") or phases[0]
    start = phases.index(target)
    rerun = [p for p in phases[start:] if state.get("phases", {}).get(p, {}).get("status") in ("done", "running", "stale") or p == target]
    gates = [p["gate"] for p in manifest(root)["phases"] if p["id"] in rerun]

    for p in rerun:
        state.setdefault("phases", {}).setdefault(p, {})["status"] = "stale"
    state["run_status"] = "in_progress"
    state["updated_at"] = now()
    write_json(root / "adlc/.state/run_state.json", state)
    run_script(root, "state.py", "refresh")
    if gate_mode(root) == "local":
        for g in gates:
            run_script(root, "adlc_gate.py", "supersede", "--gate", g, "--reason", f"change: {args.summary[:120]}")

    record = {
        "id": f"CHG-{uuid.uuid4().hex[:6]}", "at": now(), "type": args.type, "summary": args.summary,
        "ids": [i.strip() for i in (args.ids or "").split(",") if i.strip()],
        "re_enter_at": target, "re_run": rerun, "gates_to_re_request": gates, "why": why,
    }
    path = root / "adlc/.state/changes.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    audit("change.routed", target, None, {k: record[k] for k in ("id", "type", "re_enter_at", "gates_to_re_request")})
    print(f"{record['id']}: re-enter at /{target}. {why}")
    print(f"Re-run, in order: {', '.join('/' + p for p in rerun)}")
    print(f"Gates to request again: {', '.join(gates)}")
    return 0


def cmd_changes(_args) -> int:
    path = repo_root() / "adlc/.state/changes.jsonl"
    if not path.exists():
        print("No changes recorded.")
        return 0
    for line in path.read_text(encoding="utf-8").splitlines():
        c = json.loads(line)
        print(f"{c['id']}  {c['at']}  {c['type']:<12} → /{c['re_enter_at']}  gates {', '.join(c['gates_to_re_request'])}  {c['summary']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("diagnose")
    c = sub.add_parser("change")
    c.add_argument("--type", required=True)
    c.add_argument("--summary", required=True)
    c.add_argument("--ids")
    c.add_argument("--phase", help="for wording changes: which phase's artifact changed")
    sub.add_parser("changes")
    args = ap.parse_args()
    return {"diagnose": cmd_diagnose, "change": cmd_change, "changes": cmd_changes}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
