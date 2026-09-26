#!/usr/bin/env python3
"""
run_evals.py — lightweight scorer for the Requirements Agent eval scenarios.

This does NOT run the agent. Anthropic ships the eval *format and method*, not a
runner; the agent run is a deliberate human/CI step (see README.md). This script
scores the **deterministic** assertions of each scenario against an already-produced
run output tree, so the checkable part is automated and repeatable. The
`qualitative_review` items are for /evaluate-run's validator or a human reviewer.

It reuses `validate_requirements.py` for the `lint_clean` check, so there is one
source of truth for mechanical defects.

Usage:
  # after running the agent on the fixture corpus (or any real run):
  python run_evals.py --output-dir <path/to/outputs> [--skill generate-brd] [--scenario BRD-1] [--json]
  python run_evals.py --selftest      # validate evals.json + fixtures, no run needed

Exit code: 0 unless --strict and a deterministic check failed (then 1). --selftest
returns 0/1 on its own checks.
Dependency-free (stdlib only).
"""

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVALS_FILE = HERE / "evals.json"
SCRIPTS_DIR = HERE.parent / ".claude" / "skills" / "requirements-agent" / "scripts"


def _load_evals():
    return json.loads(EVALS_FILE.read_text(encoding="utf-8"))


def _import_validator():
    """Import lint_file from validate_requirements.py by path (no install needed)."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        import validate_requirements  # type: ignore
        return validate_requirements
    except Exception:
        return None


def _check(check, output_dir, validator):
    """Run one deterministic check; return (passed, evidence)."""
    ctype = check.get("type")
    rel = check.get("path", "")
    target = output_dir / rel if rel else output_dir
    if ctype == "file_exists":
        return (target.is_file(), f"{rel} {'found' if target.is_file() else 'MISSING'}")
    if ctype == "file_absent":
        return (not target.exists(), f"{rel} {'absent (ok)' if not target.exists() else 'present (unexpected)'}")
    if ctype in ("contains", "not_contains"):
        if not target.is_file():
            return (False, f"{rel} MISSING — cannot check pattern")
        text = target.read_text(encoding="utf-8", errors="ignore")
        hit = re.search(check.get("pattern", ""), text) is not None
        if ctype == "contains":
            return (hit, f"pattern {'found' if hit else 'NOT found'} in {rel}")
        return (not hit, f"pattern {'absent (ok)' if not hit else 'unexpectedly present'} in {rel}")
    if ctype == "lint_clean":
        if validator is None:
            return (False, "validate_requirements.py not importable")
        if not target.is_file():
            return (False, f"{rel} MISSING — cannot lint")
        findings = validator.lint_file(target)
        errors = [f for f in findings if f.get("severity") == "error"]
        ev = "no error-severity lint findings" if not errors else \
            f"{len(errors)} lint error(s): " + "; ".join(f"{e['rule']}:{e['message']}" for e in errors[:3])
        return (not errors, ev)
    return (False, f"unknown check type '{ctype}'")


def score(output_dir: Path, skill=None, scenario_id=None):
    data = _load_evals()
    validator = _import_validator()
    results = []
    for sc in data["scenarios"]:
        if skill and sc["skill"] != skill:
            continue
        if scenario_id and sc["id"] != scenario_id:
            continue
        checks = []
        for chk in sc.get("deterministic", []):
            passed, evidence = _check(chk, output_dir, validator)
            checks.append({"check": chk, "passed": passed, "evidence": evidence})
        det_pass = sum(1 for c in checks if c["passed"])
        results.append({
            "id": sc["id"], "skill": sc["skill"], "name": sc["name"],
            "deterministic": checks,
            "deterministic_summary": {"passed": det_pass, "total": len(checks)},
            "qualitative_review": sc.get("qualitative_review", []),
        })
    return results


def _print_human(results):
    any_fail = False
    for r in results:
        ds = r["deterministic_summary"]
        head = f"[{r['id']}] {r['skill']} — {r['name']}: deterministic {ds['passed']}/{ds['total']}"
        print(head)
        for c in r["deterministic"]:
            mark = "ok " if c["passed"] else "FAIL"
            if not c["passed"]:
                any_fail = True
            print(f"    [{mark}] {c['evidence']}")
        if r["qualitative_review"]:
            print("    qualitative (judge with /evaluate-run or a human):")
            for q in r["qualitative_review"]:
                print(f"      - {q}")
    return any_fail


def _selftest():
    ok = True
    def chk(label, cond):
        nonlocal ok
        print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
        ok = ok and cond
    try:
        data = _load_evals()
        chk("evals.json parses", True)
    except Exception as e:
        print(f"  [FAIL] evals.json parses: {e}")
        return 1
    chk("has scenarios", bool(data.get("scenarios")))
    for f in data.get("fixture_corpus", []):
        chk(f"fixture exists: {f}", (HERE / f).is_file())
    known = {"file_exists", "file_absent", "contains", "not_contains", "lint_clean"}
    req_keys = {"id", "skill", "name", "gap", "prompt", "expected_behavior"}
    for sc in data.get("scenarios", []):
        chk(f"{sc.get('id','?')} has required keys", req_keys.issubset(sc))
        for c in sc.get("deterministic", []):
            chk(f"{sc.get('id','?')} check type '{c.get('type')}' known", c.get("type") in known)
    chk("validate_requirements importable", _import_validator() is not None)
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Score Requirements Agent eval scenarios against a produced run output tree.")
    ap.add_argument("--output-dir", help="Path to a produced outputs/ directory.")
    ap.add_argument("--skill", help="Only score scenarios for this skill.")
    ap.add_argument("--scenario", help="Only score this scenario id.")
    ap.add_argument("--json", action="store_true", help="Emit results as JSON.")
    ap.add_argument("--strict", action="store_true", help="Exit 1 if any deterministic check fails.")
    ap.add_argument("--selftest", action="store_true", help="Validate evals.json + fixtures and exit.")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.output_dir:
        ap.error("provide --output-dir (a produced outputs/ dir) or --selftest")

    out = Path(args.output_dir)
    if not out.is_dir():
        print(f"output dir not found: {out}", file=sys.stderr)
        return 2
    results = score(out, args.skill, args.scenario)
    if args.json:
        print(json.dumps({"results": results}, indent=2))
        any_fail = any(not c["passed"] for r in results for c in r["deterministic"])
    else:
        any_fail = _print_human(results)
    return 1 if (args.strict and any_fail) else 0


if __name__ == "__main__":
    sys.exit(main())
