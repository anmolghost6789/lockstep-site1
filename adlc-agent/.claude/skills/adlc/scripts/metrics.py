#!/usr/bin/env python3
"""Delivery metrics for an ADLC run, computed from the run's own records.

  metrics.py show                                   print the metrics
  metrics.py push --registry https://… --token lsk_…   send them to your Lockstep registry (opt-in)

What is measured, per phase: time in phase, time waiting for approval, rejections and rework;
across the run: bolts and tests, evaluation results, agents and models used, policy blocks,
routed changes, and success criteria met. Written to adlc/.state/metrics.json.

The payload holds numbers, IDs and names of agents/models only. It never includes artifact
text, inputs, prompts, code or personal data; `push` refuses to send anything else.
The project is identified by a salted hash, not by name. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

from _common import load_json, manifest, now, repo_root, write_json

SCHEMA = "lockstep-telemetry-1.0"


def ts(v: str | None):
    return dt.datetime.fromisoformat(v) if v else None


def hours(a, b) -> float | None:
    return None if not a or not b else round((b - a).total_seconds() / 3600, 3)


def read_audit(root):
    p = root / "adlc/.audit/audit.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def project_id(root) -> str:
    remote = subprocess.run(["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True, cwd=root).stdout.strip()
    basis = remote or str(root.resolve())
    return hashlib.sha256(("lockstep:" + basis).encode()).hexdigest()[:16]


def pack_info(root) -> dict:
    installed = load_json(root / ".lockstep/installed.json", {}) or {}
    manifest_file = load_json(root / "lockstep-pack.json", {}) or {}
    return {"name": installed.get("name") or manifest_file.get("name", "adlc"), "version": installed.get("version") or manifest_file.get("version", "unversioned")}


def compute(root) -> dict:
    audit = read_audit(root)
    state = load_json(root / "adlc/.state/run_state.json", {}) or {}
    phases_out = []
    for ph in manifest(root)["phases"]:
        pid, gate = ph["id"], ph["gate"]
        ps = state.get("phases", {}).get(pid, {})
        ev = [e for e in audit if e.get("phase") == pid or e.get("gate") == gate]
        started = [ts(e["ts"]) for e in ev if e["event"] == "phase.started"]
        completed = [ts(e["ts"]) for e in ev if e["event"] == "phase.completed"]
        requested = [ts(e["ts"]) for e in ev if e["event"] == "gate.requested"]
        approved = [ts(e["ts"]) for e in ev if e["event"] == "gate.approved"]
        g = load_json(root / f"adlc/.gates/{gate}.json", {}) or {}
        if not approved and g.get("approved_at"):
            approved = [ts(g["approved_at"])]
        phases_out.append({
            "phase": pid,
            "status": ps.get("status", "pending"),
            "runs": len(started),
            "time_in_phase_h": hours(started[0], completed[-1]) if started and completed else None,
            "approval_wait_h": hours(requested[-1], approved[-1]) if requested and approved and approved[-1] >= requested[-1] else None,
            "rejections": sum(1 for e in ev if e["event"] == "gate.rejected"),
            "gate_requests": len(requested),
            "denied_approvals": sum(1 for e in ev if e["event"] == "gate.denied"),
        })

    units_text = (root / "adlc/03-units.yaml").read_text(encoding="utf-8") if (root / "adlc/03-units.yaml").exists() else ""
    tests = [int(x) for x in re.findall(r"tests_passed:\s*(\d+)", units_text)]
    card = load_json(root / "adlc/04-scorecard.json", {}) or {}
    mets = card.get("metrics", [])
    routing = load_json(root / "adlc/.state/routing.json", {}) or {}
    chosen = [v["chosen"] for k, v in routing.items() if isinstance(v, dict) and v.get("chosen")]
    changes_p = root / "adlc/.state/changes.jsonl"
    changes = [json.loads(l) for l in changes_p.read_text(encoding="utf-8").splitlines() if l.strip()] if changes_p.exists() else []
    by_type: dict[str, int] = {}
    for c in changes:
        by_type[c["type"]] = by_type.get(c["type"], 0) + 1

    backlog = (root / "adlc/06-backlog.md").read_text(encoding="utf-8") if (root / "adlc/06-backlog.md").exists() else ""
    sc_rows = [l for l in backlog.splitlines() if re.search(r"\bSC-\d{3}\b", l) and l.strip().startswith("|")]
    sc_met = sum(1 for l in sc_rows if re.search(r"\b(yes|met)\b", l, re.I))

    first = min((ts(e["ts"]) for e in audit), default=None)
    last = max((ts(e["ts"]) for e in audit), default=None)
    return {
        "schema": SCHEMA,
        "generated_at": now(),
        "project": project_id(root),
        "run_id": state.get("run_id"),
        "pack": pack_info(root),
        "run": {"status": state.get("run_status"), "elapsed_h": hours(first, last)},
        "phases": phases_out,
        "build": {"units": len(re.findall(r"^\s*-\s*id:\s*UNIT-\d{3}", units_text, re.M)), "bolts": len(re.findall(r"^\s*-\s*id:\s*BOLT-\d{3}", units_text, re.M)), "tests_passed": sum(tests)},
        "evaluation": {"verdict": card.get("verdict"), "cases": card.get("evaluated_build", {}).get("cases"), "metrics_total": len(mets), "metrics_passed": sum(1 for m in mets if m.get("passed"))},
        "routing": {"agents": sorted({c["agent"] for c in chosen}), "models": sorted({c["model"] for c in chosen})},
        "policy": {"blocks": sum(1 for e in audit if e["event"] == "policy.blocked"), "checks_failed": sum(1 for e in audit if e["event"] == "policy.checked" and not e.get("data", {}).get("passed", True))},
        "changes": {"count": len(changes), "by_type": by_type},
        "outcomes": {"success_criteria": len(sc_rows), "met": sc_met},
    }


SAFE_KEYS = {"schema", "generated_at", "project", "run_id", "pack", "name", "version", "run", "status", "elapsed_h", "phases", "phase", "runs",
             "time_in_phase_h", "approval_wait_h", "rejections", "gate_requests", "denied_approvals", "build", "units", "bolts", "tests_passed",
             "evaluation", "verdict", "cases", "metrics_total", "metrics_passed", "routing", "agents", "models", "policy", "blocks", "checks_failed",
             "changes", "count", "by_type", "outcomes", "success_criteria", "met"}


def assert_safe(obj, path="") -> None:
    """Refuse to send anything outside the fixed schema, so no content can leak into telemetry."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if path.endswith("by_type"):
                if not re.fullmatch(r"[a-z_]{1,20}", k):
                    raise ValueError(f"unexpected key {k}")
            elif k not in SAFE_KEYS:
                raise ValueError(f"unexpected field {path}.{k}")
            assert_safe(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for v in obj:
            assert_safe(v, path)
    elif isinstance(obj, str) and len(obj) > 64:
        raise ValueError(f"{path} is too long to be an identifier")


def cmd_show(_args) -> int:
    root = repo_root()
    m = compute(root)
    write_json(root / "adlc/.state/metrics.json", m)
    print(f"Run {m['run_id']} ({m['run']['status']}), pack {m['pack']['name']} {m['pack']['version']}, elapsed {m['run']['elapsed_h']} h")
    print(f"{'phase':<19}{'status':<10}{'in phase h':>11}{'approval h':>11}{'rejects':>9}{'requests':>10}")
    for p in m["phases"]:
        print(f"{p['phase']:<19}{p['status']:<10}{str(p['time_in_phase_h'] or '-'):>11}{str(p['approval_wait_h'] or '-'):>11}{p['rejections']:>9}{p['gate_requests']:>10}")
    e = m["evaluation"]
    print(f"Build: {m['build']['units']} units, {m['build']['bolts']} bolts, {m['build']['tests_passed']} tests passing")
    print(f"Evaluation: {e['verdict']}, {e['metrics_passed']}/{e['metrics_total']} metrics on {e['cases']} cases")
    print(f"Agents: {', '.join(m['routing']['agents']) or '-'}; policy blocks: {m['policy']['blocks']}; changes: {m['changes']['count']}")
    print(f"Outcomes: {m['outcomes']['met']}/{m['outcomes']['success_criteria']} success criteria met")
    return 0


def cmd_push(args) -> int:
    root = repo_root()
    m = compute(root)
    try:
        assert_safe(m)
    except ValueError as e:
        print(f"Not sent: {e}")
        return 3
    req = urllib.request.Request(args.registry.rstrip("/") + "/api/registry/telemetry", data=json.dumps(m).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {args.token}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"Sent metrics for run {m['run_id']}: HTTP {r.status}")
            return 0
    except urllib.error.HTTPError as e:
        print(f"Registry refused the metrics: HTTP {e.code} {e.read().decode()[:200]}")
        return 1
    except urllib.error.URLError as e:
        print(f"Could not reach the registry: {e.reason}")
        return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    p = sub.add_parser("push"); p.add_argument("--registry", required=True); p.add_argument("--token", required=True)
    args = ap.parse_args()
    return {"show": cmd_show, "push": cmd_push}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
