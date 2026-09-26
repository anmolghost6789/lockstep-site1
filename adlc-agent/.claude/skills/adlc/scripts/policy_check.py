#!/usr/bin/env python3
"""Run a phase's policy pack (config/project_config.json > policy_packs).

  policy_check.py --phase build-orchestrate

Each check returns pass, fail, or external. "external" checks are delegated to CI:
they pass only when CI has written evidence to adlc/.state/evidence/<check>.json with
{"passed": true}. Results go to adlc/.state/policy/<phase>.json and the audit log.
Exit 1 if any check fails.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

from _common import load_json, now, phase_by_id, repo_root, write_json
from audit_log import append as audit

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                                   # AWS access key
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),                            # generic API key style
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),                      # GitHub tokens
    re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
]
PII_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@(?!acme\.example\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "aadhaar": re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b"),
    "pan": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}


def _luhn(number: str) -> bool:
    digits = [int(d) for d in re.sub(r"\D", "", number)]
    if len(digits) < 13:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _artifact_texts(root):
    for path in sorted((root / "adlc").glob("0*-*.*")):
        yield path, path.read_text(encoding="utf-8", errors="replace")


def check_no_secrets(root, phase):
    hits = [f"{p.name}: {pat.pattern[:30]}" for p, t in _artifact_texts(root) for pat in SECRET_PATTERNS if pat.search(t)]
    return ("fail", hits) if hits else ("pass", [])


def check_pii_scan(root, phase):
    hits = []
    for p, t in _artifact_texts(root):
        for kind, pat in PII_PATTERNS.items():
            for m in pat.finditer(t):
                if kind == "card" and not _luhn(m.group(0)):
                    continue
                hits.append(f"{p.name}: possible {kind}")
    return ("fail", sorted(set(hits))) if hits else ("pass", [])


def check_trace_ids_present(root, phase):
    result = load_json(root / "adlc/.state/validation" / f"{phase['id']}.json")
    if not result:
        return "fail", ["run validate_artifact.py first"]
    return ("pass", []) if result["passed"] else ("fail", result["errors"][:5])


def check_model_pins_approved(root, phase):
    cfg = load_json(root / "config/project_config.json")
    approved = set(load_json(root / "config/governance/model_policy.json")["approved_models"])
    bad = [f"{k}: {v}" for k, v in cfg["models"].items() if k != "description" and v not in approved]
    return ("fail", bad) if bad else ("pass", [])


def check_mcp_allowlist(root, phase):
    allowed = set(load_json(root / "config/governance/mcp_allowlist.json")["servers"])
    configured = set((load_json(root / ".mcp.json", {}) or {}).get("mcpServers", {}))
    extra = sorted(configured - allowed)
    return ("fail", [f"not allow-listed: {s}" for s in extra]) if extra else ("pass", [])


def check_tests_per_bolt(root, phase):
    text = (root / "adlc/03-units.yaml").read_text(encoding="utf-8") if (root / "adlc/03-units.yaml").exists() else ""
    bolts = re.findall(r"^\s*-\s*id:\s*(BOLT-\d{3})", text, re.M)
    if not bolts:
        return "fail", ["no bolts found in 03-units.yaml"]
    blocks = re.split(r"^\s*-\s*id:\s*BOLT-\d{3}", text, flags=re.M)[1:]
    missing = [b for b, block in zip(bolts, blocks) if not re.search(r"tests_passed:\s*[1-9]", block)]
    return ("fail", [f"{b} has no passing tests" for b in missing]) if missing else ("pass", [])


def check_evaluator_independence(root, phase):
    card = load_json(root / "adlc/04-scorecard.json", {}) or {}
    units = (root / "adlc/03-units.yaml").read_text(encoding="utf-8") if (root / "adlc/03-units.yaml").exists() else ""
    evaluator = card.get("evaluator", {}).get("agent")
    authors = set(re.findall(r"built_by:\s*([\w\-]+)", units))
    if not evaluator:
        return "fail", ["scorecard.evaluator.agent missing"]
    return ("fail", [f"{evaluator} also built code under evaluation"]) if evaluator in authors else ("pass", [])


def check_thresholds_from_aiprs(root, phase):
    card = load_json(root / "adlc/04-scorecard.json", {}) or {}
    bad = [m["id"] for m in card.get("metrics", []) if not any(t.startswith(("NFR-", "SC-")) for t in m.get("trace", []))]
    return ("fail", [f"{b} threshold not traced to an NFR or SC" for b in bad]) if bad else ("pass", [])


def check_min_eval_cases(root, phase):
    cfg = load_json(root / "config/project_config.json")
    card = load_json(root / "adlc/04-scorecard.json", {}) or {}
    n = card.get("evaluated_build", {}).get("cases", 0)
    need = cfg["evaluation"]["min_eval_cases"]
    return ("pass", []) if n >= need else ("fail", [f"{n} cases; policy requires {need}"])


def _section(text, name):
    m = re.search(rf"^##\s+{re.escape(name)}\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return (m.group(1).strip() if m else "")


def check_rollback_plan(root, phase):
    text = (root / "adlc/05-release.md").read_text(encoding="utf-8")
    body = _section(text, "Rollback Plan")
    return ("pass", []) if len(body) > 80 else ("fail", ["Rollback Plan section is missing or too thin"])


def check_versions_pinned(root, phase):
    body = _section((root / "adlc/05-release.md").read_text(encoding="utf-8"), "Versions")
    loose = re.findall(r"\b(latest|main|HEAD|\*)\b", body)
    return ("fail", [f"unpinned version: {x}" for x in loose]) if loose else ("pass", [])


def _external(name):
    def run(root, phase):
        ev = load_json(root / "adlc/.state/evidence" / f"{name}.json")
        if not ev:
            return "external", [f"waiting for CI evidence at adlc/.state/evidence/{name}.json"]
        return ("pass", []) if ev.get("passed") else ("fail", ev.get("findings", ["CI reported failure"]))
    return run


CHECKS = {
    "no_secrets": check_no_secrets,
    "pii_scan": check_pii_scan,
    "trace_ids_present": check_trace_ids_present,
    "model_pins_approved": check_model_pins_approved,
    "mcp_allowlist": check_mcp_allowlist,
    "tests_per_bolt": check_tests_per_bolt,
    "evaluator_independence": check_evaluator_independence,
    "thresholds_from_aiprs": check_thresholds_from_aiprs,
    "min_eval_cases": check_min_eval_cases,
    "rollback_plan": check_rollback_plan,
    "versions_pinned": check_versions_pinned,
    "license_scan": _external("license_scan"),
    "sbom_present": _external("sbom_present"),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", required=True)
    args = ap.parse_args()
    root = repo_root()
    phase = phase_by_id(root, args.phase)
    pack = load_json(root / "config/project_config.json")["policy_packs"][args.phase]
    results = {}
    for name in pack:
        status, findings = CHECKS[name](root, phase)
        results[name] = {"status": status, "findings": findings}
    failed = [n for n, r in results.items() if r["status"] != "pass"]
    report = {"phase": args.phase, "checked_at": now(), "passed": not failed, "results": results}
    write_json(root / "adlc/.state/policy" / f"{args.phase}.json", report)
    audit("policy.checked", args.phase, phase["gate"], {"passed": not failed, "failed": failed})
    for name, r in results.items():
        print(f"{r['status'].upper():<8} {name}" + (f"  ({'; '.join(r['findings'][:3])})" if r["findings"] else ""))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
