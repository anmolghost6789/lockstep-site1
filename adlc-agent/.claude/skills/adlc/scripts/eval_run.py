#!/usr/bin/env python3
"""ADLC evaluation runner. Runs an evaluation suite and writes adlc/04-scorecard.json.

  eval_run.py run      [--suite adlc/evals/suite.json]       run the suite, write the scorecard
  eval_run.py compare  --suite A.json --against B.json      same cases, two systems: with vs without a pack or change
  eval_run.py thresholds                                     show the thresholds read from the approved AIPRS

Suite file (JSON):
{
  "intent_id": "INT-0192",
  "dataset": "adlc/evals/cases.jsonl",          # one JSON object per line: {"id", "input", "expected", ...}
  "system": {"command": "python3 app/predict.py"},  # reads a case on stdin, prints JSON on stdout
  #   or {"predictions": "adlc/evals/predictions.jsonl"}  (precomputed: {"id", "output", "latency_s", "cost_usd"})
  "evaluator": {"agent": "adlc-evaluator", "model": "claude-opus-5-5"},
  "metrics": [
    {"id": "EVAL-001", "name": "classification accuracy", "type": "accuracy", "field": "risk", "trace": "NFR-001"},
    {"id": "EVAL-002", "name": "high-risk recall", "type": "recall", "field": "risk", "positive": "high", "trace": "NFR-003"},
    {"id": "EVAL-003", "name": "auto-approved high-risk cases", "type": "count_where",
     "where": {"expected.risk": "high", "output.action": "auto_approve"}, "trace": "NFR-002"},
    {"id": "EVAL-004", "name": "p95 latency (s)", "type": "latency_p95", "trace": "NFR-004"},
    {"id": "EVAL-005", "name": "cost per case (USD)", "type": "cost_mean", "trace": "NFR-005"}
  ]
}

Thresholds are never set in the suite. Each metric's `trace` names an NFR or SC in adlc/01-aiprs.md,
and the threshold is read from that row's Threshold/Target column (e.g. "≥ 0.99", "0", "≤ 5 s").
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

from _common import load_json, now, repo_root, sha256_file, write_json

COMPARATORS = {"≥": ">=", ">=": ">=", "≤": "<=", "<=": "<=", "=": "==", "==": "==", "<": "<", ">": ">"}


# --------------------------------------------------------------------------- thresholds

def parse_threshold(cell: str) -> tuple[str, float] | None:
    """'≥ 0.99' -> ('>=', 0.99); '0 exceptions' -> ('==', 0); '≤ 5 s' -> ('<=', 5)."""
    cell = cell.strip()
    m = re.match(r"^(≥|>=|≤|<=|==|=|<|>)?\s*\$?(-?\d+(?:\.\d+)?)", cell)
    if not m:
        return None
    op = COMPARATORS.get(m.group(1) or "==", "==")
    return op, float(m.group(2))


def aiprs_thresholds(root: Path) -> dict[str, tuple[str, float, str]]:
    """Read NFR and SC thresholds from the approved AIPRS tables: {ID: (op, value, raw)}."""
    path = root / "adlc/01-aiprs.md"
    if not path.exists():
        return {}
    out: dict[str, tuple[str, float, str]] = {}
    header: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            header = []
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].lower() == "id":
            header = [c.lower() for c in cells]
            continue
        if not header or set(cells[0]) <= {"-", ":", " "}:
            continue
        rid = cells[0]
        if not re.fullmatch(r"(NFR|SC)-\d{3}", rid):
            continue
        col = next((header.index(h) for h in ("threshold", "target") if h in header), None)
        if col is None or col >= len(cells):
            continue
        parsed = parse_threshold(cells[col])
        if parsed:
            out[rid] = (parsed[0], parsed[1], cells[col])
    return out


def passes(value: float, op: str, threshold: float) -> bool:
    return {
        ">=": value >= threshold - 1e-12,
        "<=": value <= threshold + 1e-12,
        "==": abs(value - threshold) < 1e-9,
        ">": value > threshold,
        "<": value < threshold,
    }[op]


# --------------------------------------------------------------------------- running the system

def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def run_system(root: Path, system: dict, cases: list[dict]) -> list[dict]:
    if "predictions" in system:
        preds = {p["id"]: p for p in read_jsonl(root / system["predictions"])}
        return [{"id": c["id"], **preds.get(c["id"], {"output": None, "error": "missing prediction"})} for c in cases]
    cmd = shlex.split(system["command"])
    results = []
    for c in cases:
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(cmd, input=json.dumps(c.get("input", c)), capture_output=True, text=True, timeout=system.get("timeout_s", 120), cwd=root)
            latency = time.perf_counter() - t0
            if proc.returncode != 0:
                results.append({"id": c["id"], "output": None, "error": proc.stderr.strip()[:300], "latency_s": latency})
                continue
            out = json.loads(proc.stdout or "null")
            cost = out.pop("cost_usd", None) if isinstance(out, dict) else None
            results.append({"id": c["id"], "output": out, "latency_s": latency, "cost_usd": cost})
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            results.append({"id": c["id"], "output": None, "error": type(e).__name__, "latency_s": time.perf_counter() - t0})
    return results


# --------------------------------------------------------------------------- metrics

def get(obj, dotted: str):
    for part in dotted.split("."):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    v = sorted(values)
    k = (len(v) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] if lo == hi else v[lo] + (v[hi] - v[lo]) * (k - lo)


def compute(metric: dict, cases: list[dict], results: list[dict]) -> tuple[float, list[str]]:
    """Returns (value, ids of failing cases for human review)."""
    by_id = {r["id"]: r for r in results}
    rows = [(c, by_id.get(c["id"], {})) for c in cases]
    t = metric["type"]
    if t in ("accuracy", "recall", "precision"):
        field = metric["field"]
        pos = metric.get("positive")
        exp = [get(c, f"expected.{field}") for c, _ in rows]
        got = [get(r, f"output.{field}") for _, r in rows]
        if t == "accuracy":
            ok = [e == g for e, g in zip(exp, got)]
            fails = [c["id"] for (c, _), o in zip(rows, ok) if not o]
            return (sum(ok) / len(ok) if ok else float("nan")), fails
        if t == "recall":
            idx = [i for i, e in enumerate(exp) if e == pos]
            hit = [i for i in idx if got[i] == pos]
            return (len(hit) / len(idx) if idx else float("nan")), [rows[i][0]["id"] for i in idx if i not in hit]
        idx = [i for i, g in enumerate(got) if g == pos]
        hit = [i for i in idx if exp[i] == pos]
        return (len(hit) / len(idx) if idx else float("nan")), [rows[i][0]["id"] for i in idx if i not in hit]
    if t == "count_where":
        where = metric["where"]
        match = []
        for c, r in rows:
            merged = {"expected": c.get("expected", {}), "input": c.get("input", {}), "output": r.get("output") or {}}
            if all(get(merged, k) == v for k, v in where.items()):
                match.append(c["id"])
        return float(len(match)), match
    if t == "error_rate":
        errs = [c["id"] for c, r in rows if r.get("error")]
        return (len(errs) / len(rows) if rows else float("nan")), errs
    if t == "latency_p95":
        return percentile([r["latency_s"] for _, r in rows if r.get("latency_s") is not None], 0.95), []
    if t == "cost_mean":
        costs = [r["cost_usd"] for _, r in rows if isinstance(r.get("cost_usd"), (int, float))]
        return (sum(costs) / len(costs) if costs else float("nan")), []
    raise SystemExit(f"Unknown metric type: {t}")


CATEGORY = {"accuracy": "llm", "recall": "llm", "precision": "llm", "count_where": "security", "error_rate": "functional", "latency_p95": "performance", "cost_mean": "cost"}


def evaluate(root: Path, suite: dict) -> dict:
    thresholds = aiprs_thresholds(root)
    cases = read_jsonl(root / suite["dataset"])
    results = run_system(root, suite["system"], cases)
    raw_dir = root / "adlc/.state/eval/raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"results-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
    raw_path.write_text("\n".join(json.dumps(r) for r in results) + "\n", encoding="utf-8")

    metrics, problems, review = [], [], set()
    for m in suite["metrics"]:
        value, fails = compute(m, cases, results)
        th = thresholds.get(m.get("trace", ""))
        if not th:
            problems.append(f"{m['id']}: no threshold for {m.get('trace')} in the approved AIPRS; route back to /discover-define")
            op, threshold, passed = "==", float("nan"), False
        else:
            op, threshold, _raw = th
            passed = not math.isnan(value) and passes(value, op, threshold)
        review.update(fails[:10])
        metrics.append({
            "id": m["id"], "category": m.get("category", CATEGORY.get(m["type"], "functional")), "name": m["name"],
            "threshold": None if math.isnan(threshold) else threshold, "comparator": op,
            "value": None if math.isnan(value) else round(value, 6), "passed": passed,
            "trace": [m["trace"]] if m.get("trace") else [], "evidence": [str(raw_path.relative_to(root))],
        })
    verdict = "pass" if metrics and all(x["passed"] for x in metrics) and not problems else "fail"
    ds = root / suite["dataset"]
    units = root / "adlc/03-units.yaml"
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=root).stdout.strip() or "uncommitted"
    scorecard = {
        "intent_id": suite.get("intent_id", "unknown"),
        "evaluated_at": now(),
        "evaluated_build": {
            "commit": commit,
            "units_sha256": sha256_file(units) if units.exists() else None,
            "dataset": {"path": suite["dataset"], "version": suite.get("dataset_version", "1"), "sha256": sha256_file(ds)},
            "cases": len(cases),
        },
        "metrics": metrics,
        "verdict": verdict,
        "route_back": None if verdict == "pass" else ("discover-define" if problems else "build-orchestrate"),
        "evaluator": suite.get("evaluator", {"agent": "adlc-evaluator", "model": "unknown"}),
        "problems": problems,
    }
    # Failed and borderline cases for the QA lead, without copying case content.
    review_path = root / "adlc/.state/eval/human_review.jsonl"
    review_path.write_text("\n".join(json.dumps({"id": i, "reason": "failed a metric"}) for i in sorted(review)) + ("\n" if review else ""), encoding="utf-8")
    return scorecard


# --------------------------------------------------------------------------- commands

def cmd_run(args) -> int:
    root = repo_root()
    suite = load_json(root / args.suite)
    if suite is None:
        print(f"No suite at {args.suite}. See `eval_run.py --help` for the format.")
        return 2
    card = evaluate(root, suite)
    write_json(root / "adlc/04-scorecard.json", card)
    passed = sum(m["passed"] for m in card["metrics"])
    print(f"{card['verdict'].upper()}: {passed}/{len(card['metrics'])} metrics on {card['evaluated_build']['cases']} cases. Wrote adlc/04-scorecard.json")
    for m in card["metrics"]:
        print(f"  {'✓' if m['passed'] else '✗'} {m['id']} {m['name']}: {m['value']} (needs {m['comparator']} {m['threshold']}, {', '.join(m['trace'])})")
    for p in card["problems"]:
        print(f"  ! {p}")
    return 0 if card["verdict"] == "pass" else 1


def cmd_compare(args) -> int:
    root = repo_root()
    a, b = load_json(root / args.suite), load_json(root / args.against)
    ca, cb = evaluate(root, a), evaluate(root, b)
    rows = []
    for ma in ca["metrics"]:
        mb = next((m for m in cb["metrics"] if m["id"] == ma["id"]), None)
        if not mb:
            continue
        delta = None if ma["value"] is None or mb["value"] is None else round(ma["value"] - mb["value"], 6)
        rows.append({"id": ma["id"], "name": ma["name"], "with": ma["value"], "without": mb["value"], "delta": delta, "passed_with": ma["passed"], "passed_without": mb["passed"]})
    report = {"compared_at": now(), "with": args.suite, "without": args.against, "cases": ca["evaluated_build"]["cases"], "metrics": rows}
    out = root / "adlc/.state/eval/comparison.json"
    write_json(out, report)
    print(f"Compared on {report['cases']} cases (with = {args.suite}, without = {args.against}):")
    for r in rows:
        print(f"  {r['id']} {r['name']}: {r['with']} vs {r['without']} (delta {r['delta']})")
    print(f"Wrote {out.relative_to(root)}")
    return 0


def cmd_thresholds(_args) -> int:
    th = aiprs_thresholds(repo_root())
    if not th:
        print("No NFR or SC thresholds found in adlc/01-aiprs.md.")
        return 2
    for k, (op, v, raw) in sorted(th.items()):
        print(f"{k}: {op} {v}   ({raw})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--suite", default="adlc/evals/suite.json")
    c = sub.add_parser("compare"); c.add_argument("--suite", required=True); c.add_argument("--against", required=True)
    sub.add_parser("thresholds")
    args = ap.parse_args()
    return {"run": cmd_run, "compare": cmd_compare, "thresholds": cmd_thresholds}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
