#!/usr/bin/env python3
"""ADLC gate control. The only writer of adlc/.gates/.

  request --gate G1 --summary "..." [--risk low|medium|high|critical]
  approve --gate G1 [--comment "..."]
  reject  --gate G1 --comment "..."          (comment required)
  waive   --gate G1 --reason "..." [--days N] (waiver_approver role only)
  check   --gate G1                           exit 0 only if approved/waived and artifact unchanged
  supersede --gate G1 --reason "..."         mark a gate void after an upstream change (used by recover.py)
  status                                      all gates

Exit codes for check: 0 ok, 2 missing or pending, 4 artifact changed since approval,
5 rejected, 6 waiver expired. Approve/reject/waive: 3 not permitted.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

from _common import (
    identity,
    load_json,
    now,
    parse_ts,
    phase_by_gate,
    repo_root,
    roles_for,
    sha256_file,
    write_json,
)
from audit_log import append as audit


def _cfg(root):
    return load_json(root / "config/governance/gate_roles.json")


def _gate_path(root, gate):
    return root / "adlc/.gates" / f"{gate}.json"


def _required_roles(cfg, gate, record) -> list[str]:
    spec = cfg["gates"][gate]
    roles = list(spec["roles"])
    extra = spec.get("additional_roles_if_risk", {}).get(record.get("risk") or "", [])
    return roles + [r for r in extra if r not in roles]


def _satisfied(cfg, gate, record) -> bool:
    need = cfg["gates"][gate].get("min_approvals", 1)
    approvals = [d for d in record["decisions"] if d["decision"] == "approve"]
    for role in _required_roles(cfg, gate, record):
        if len({d["actor"] for d in approvals if role in d["roles"]}) < need:
            return False
    return True


def cmd_request(args) -> int:
    root = repo_root()
    cfg = _cfg(root)
    phase = phase_by_gate(root, args.gate)
    artifact = root / phase["artifact"]
    if not artifact.exists():
        print(f"Cannot request {args.gate}: {phase['artifact']} does not exist.")
        return 2
    digest = sha256_file(artifact)
    existing = load_json(_gate_path(root, args.gate))
    if existing and existing["status"] == "approved" and existing["artifact_sha256"] == digest:
        print(f"{args.gate} already approved for this exact artifact. Nothing to do.")
        return 0
    requester = identity()
    record = {
        "gate": args.gate,
        "phase": phase["id"],
        "artifact": phase["artifact"],
        "artifact_sha256": digest,
        "status": "pending",
        "risk": args.risk,
        "summary": args.summary,
        "requested_by": requester,
        "requested_at": now(),
        "decisions": [],
        "history": (existing or {}).get("history", []) + ([{k: existing[k] for k in ("status", "artifact_sha256", "requested_at")}] if existing else []),
    }
    write_json(_gate_path(root, args.gate), record)
    audit("gate.requested", phase["id"], args.gate, {"artifact": phase["artifact"], "sha256": digest, "risk": args.risk, "summary": args.summary}, requester)
    roles = ", ".join(_required_roles(cfg, args.gate, record))
    print(f"{args.gate} requested. Needs approval from: {roles}. Approver runs: /approve-gate {args.gate}")
    return 0


def _load_pending(root, gate):
    record = load_json(_gate_path(root, gate))
    if not record:
        print(f"{gate} has not been requested.")
        return None
    if record["status"] not in ("pending",):
        print(f"{gate} is {record['status']}; only pending gates accept decisions. Re-request after changes.")
        return None
    return record


def _decide(args, decision: str) -> int:
    root = repo_root()
    cfg = _cfg(root)
    record = _load_pending(root, args.gate)
    if record is None:
        return 2
    actor = identity()
    actor_roles = roles_for(root, actor)
    required = _required_roles(cfg, args.gate, record)
    held = sorted(set(required) & actor_roles)
    if not held:
        audit("gate.denied", record["phase"], args.gate, {"reason": "missing_role", "required": required}, actor)
        print(f"Not permitted: {actor} holds none of the required roles ({', '.join(required)}).")
        return 3
    if cfg.get("separation_of_duties", True) and actor == record["requested_by"]:
        audit("gate.denied", record["phase"], args.gate, {"reason": "separation_of_duties"}, actor)
        print("Not permitted: the requester of a gate cannot decide it (separation of duties).")
        return 3
    current = sha256_file(root / record["artifact"])
    if current != record["artifact_sha256"]:
        print(f"{record['artifact']} changed after the gate was requested. Ask the author to re-run the phase and re-request.")
        return 4
    if decision == "reject" and not args.comment:
        print("A rejection needs --comment explaining what must change.")
        return 3
    record["decisions"].append({"decision": decision, "actor": actor, "roles": held, "comment": args.comment, "at": now()})
    if decision == "reject":
        record["status"] = "rejected"
    elif _satisfied(cfg, args.gate, record):
        record["status"] = "approved"
        record["approved_at"] = now()
    write_json(_gate_path(root, args.gate), record)
    event = {"approved": "gate.approved", "rejected": "gate.rejected"}.get(record["status"], "gate.approval_recorded")
    audit(event, record["phase"], args.gate, {"roles": held, "comment": args.comment, "sha256": current}, actor)
    if record["status"] == "approved":
        print(f"{args.gate} approved by {actor} ({', '.join(held)}).")
    elif record["status"] == "rejected":
        print(f"{args.gate} rejected by {actor}. The author must address: {args.comment}")
    else:
        missing = [r for r in required if not any(r in d["roles"] for d in record["decisions"] if d["decision"] == "approve")]
        print(f"Approval recorded. {args.gate} still needs: {', '.join(missing)}.")
    return 0


def cmd_waive(args) -> int:
    root = repo_root()
    cfg = _cfg(root)
    actor = identity()
    if not set(cfg["waivers"]["roles"]) & roles_for(root, actor):
        print(f"Not permitted: waivers need one of {', '.join(cfg['waivers']['roles'])}.")
        return 3
    days = min(args.days, cfg["waivers"].get("max_validity_days", 30))
    phase = phase_by_gate(root, args.gate)
    artifact = root / phase["artifact"]
    record = load_json(_gate_path(root, args.gate)) or {
        "gate": args.gate, "phase": phase["id"], "artifact": phase["artifact"], "decisions": [], "history": [],
        "requested_by": None, "requested_at": None, "risk": None, "summary": None,
    }
    record["artifact_sha256"] = sha256_file(artifact) if artifact.exists() else None
    record["status"] = "waived"
    record["waiver"] = {
        "by": actor,
        "reason": args.reason,
        "at": now(),
        "expires_at": (dt.datetime.fromisoformat(now()) + dt.timedelta(days=days)).isoformat(timespec="seconds"),
    }
    write_json(_gate_path(root, args.gate), record)
    audit("gate.waived", phase["id"], args.gate, {"reason": args.reason, "days": days}, actor)
    print(f"{args.gate} waived for {days} days by {actor}.")
    return 0


def cmd_supersede(args) -> int:
    root = repo_root()
    record = load_json(_gate_path(root, args.gate))
    if not record:
        return 0
    record["history"] = record.get("history", []) + [{"status": record["status"], "artifact_sha256": record.get("artifact_sha256"), "requested_at": record.get("requested_at")}]
    record["status"] = "superseded"
    record["superseded"] = {"at": now(), "reason": args.reason}
    write_json(_gate_path(root, args.gate), record)
    audit("gate.superseded", record["phase"], args.gate, {"reason": args.reason})
    print(f"{args.gate} superseded: {args.reason}")
    return 0


def cmd_check(args) -> int:
    root = repo_root()
    cfg = _cfg(root)
    record = load_json(_gate_path(root, args.gate))
    phase = phase_by_gate(root, args.gate)
    if not record:
        print(f"{args.gate} ({phase['label']}) has not been requested. Run the {phase['id']} phase first.")
        return 2
    if record["status"] == "superseded":
        print(f"{args.gate} was superseded by a change ({record['superseded']['reason']}). Re-run {phase['id']} and request it again.")
        return 2
    if record["status"] == "rejected":
        last = [d for d in record["decisions"] if d["decision"] == "reject"][-1]
        print(f"{args.gate} was rejected by {last['actor']}: {last['comment']}")
        return 5
    if record["status"] == "waived":
        if parse_ts(record["waiver"]["expires_at"]) < parse_ts(now()):
            print(f"{args.gate} waiver expired on {record['waiver']['expires_at']}.")
            return 6
        print(f"{args.gate} waived by {record['waiver']['by']}: {record['waiver']['reason']}")
        return 0
    if record["status"] != "approved":
        print(f"{args.gate} is pending. Needs: {', '.join(_required_roles(cfg, args.gate, record))}. Approver runs /approve-gate {args.gate}.")
        return 2
    artifact = root / record["artifact"]
    if not artifact.exists() or sha256_file(artifact) != record["artifact_sha256"]:
        print(f"{record['artifact']} changed after {args.gate} was approved. Re-run {phase['id']} and re-request the gate.")
        return 4
    print(f"{args.gate} approved.")
    return 0


def cmd_status(_args) -> int:
    root = repo_root()
    cfg = _cfg(root)
    for gate in cfg["gates"]:
        record = load_json(_gate_path(root, gate))
        if not record:
            print(f"{gate}  not requested")
            continue
        who = ", ".join(sorted({d["actor"] for d in record["decisions"]})) or "-"
        print(f"{gate}  {record['status']:<9} {record['artifact']:<24} decided by: {who}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("request")
    r.add_argument("--gate", required=True)
    r.add_argument("--summary", required=True)
    r.add_argument("--risk", choices=["low", "medium", "high", "critical"])
    for name in ("approve", "reject"):
        p = sub.add_parser(name)
        p.add_argument("--gate", required=True)
        p.add_argument("--comment", default="")
    w = sub.add_parser("waive")
    w.add_argument("--gate", required=True)
    w.add_argument("--reason", required=True)
    w.add_argument("--days", type=int, default=14)
    sp = sub.add_parser("supersede")
    sp.add_argument("--gate", required=True)
    sp.add_argument("--reason", required=True)
    c = sub.add_parser("check")
    c.add_argument("--gate", required=True)
    sub.add_parser("status")
    args = ap.parse_args()
    return {
        "request": cmd_request,
        "approve": lambda a: _decide(a, "approve"),
        "reject": lambda a: _decide(a, "reject"),
        "waive": cmd_waive,
        "supersede": cmd_supersede,
        "check": cmd_check,
        "status": cmd_status,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
