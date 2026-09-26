#!/usr/bin/env python3
"""Agent routing: which agent and model should do each piece of work.

  route.py phase --phase build-orchestrate [--data-level confidential]
  route.py units [--units adlc/03-units.yaml]      one decision per unit, using each unit's
                                                    `needs:` and `data_level:` if present
  route.py explain --agent copilot-agent-opus      why an agent is or isn't eligible

Rules, in order: only approved agents; the agent must have every needed capability; it must be
allowed to see the data level; the evaluator must not be an agent that built the code; then the
lowest relative cost wins. Decisions are written to adlc/.state/routing.json with reasons, so
reviewers can see why work went where. Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys

from _common import load_json, now, repo_root, write_json
from audit_log import append as audit


def levels(root) -> list[str]:
    return (load_json(root / "config/project_config.json", {}) or {}).get("data_classification", {}).get("levels", ["public", "internal", "confidential", "restricted"])


def eligible(agent: dict, needs: list[str], level: str, lv: list[str], exclude: set[str]) -> tuple[bool, str]:
    if not agent.get("approved"):
        return False, "not approved"
    missing = [n for n in needs if n not in agent.get("capabilities", [])]
    if missing:
        return False, f"lacks {', '.join(missing)}"
    if lv.index(level) > lv.index(agent.get("max_data_level", "internal")):
        return False, f"not allowed to see {level} data"
    if agent["id"] in exclude:
        return False, "built the work it would evaluate"
    return True, "eligible"


def choose(root, needs: list[str], level: str, exclude: set[str] = frozenset()) -> dict:
    cat = load_json(root / "config/governance/agent_catalog.json")
    lv = levels(root)
    considered = []
    for a in cat["agents"]:
        ok, why = eligible(a, needs, level, lv, set(exclude))
        considered.append({"agent": a["id"], "eligible": ok, "reason": why, "cost": a.get("cost")})
    pool = [a for a in cat["agents"] if eligible(a, needs, level, lv, set(exclude))[0]]
    if not pool:
        return {"needs": needs, "data_level": level, "chosen": None, "considered": considered,
                "reason": "No eligible agent (" + "; ".join(f"{c['agent']}: {c['reason']}" for c in considered) + "). Ask the platform team to approve one, or split the work."}
    best = min(pool, key=lambda a: (a.get("cost", 99), a["id"]))
    return {"needs": needs, "data_level": level, "chosen": {"agent": best["id"], "harness": best["harness"], "model": best["model"]},
            "considered": considered, "reason": f"Lowest-cost approved agent with {', '.join(needs)} cleared for {level} data."}


def save(root, key: str, decision: dict):
    path = root / "adlc/.state/routing.json"
    data = load_json(path, {}) or {}
    data[key] = {**decision, "decided_at": now()}
    write_json(path, data)


def cmd_phase(args) -> int:
    root = repo_root()
    cat = load_json(root / "config/governance/agent_catalog.json")
    needs = cat["phase_needs"].get(args.phase, [])
    exclude: set[str] = set()
    if args.phase == "evaluate-validate" and cat["rules"].get("evaluator_must_differ_from_builder"):
        exclude = set((load_json(root / "adlc/.state/routing.json", {}) or {}).get("builders", []))
    d = choose(root, needs, args.data_level, exclude)
    save(root, f"phase:{args.phase}", d)
    audit("route.decided", args.phase, None, {"chosen": d["chosen"], "needs": needs})
    print(f"{args.phase}: {d['chosen']['agent'] + ' (' + d['chosen']['model'] + ')' if d['chosen'] else 'no eligible agent'}. {d['reason']}")
    return 0 if d["chosen"] else 1


def parse_units(text: str) -> list[dict]:
    units, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^\s*-\s*id:\s*(UNIT-\d{3})", line)
        if m:
            cur = {"id": m.group(1), "needs": ["coding", "testing"], "data_level": "internal"}
            units.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"^\s+needs:\s*\[([^\]]*)\]", line)
        if m:
            cur["needs"] = [x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()]
        m = re.match(r"^\s+data_level:\s*(\w+)", line)
        if m:
            cur["data_level"] = m.group(1)
    return units


def cmd_units(args) -> int:
    root = repo_root()
    path = root / args.units
    if not path.exists():
        print(f"{args.units} not found.")
        return 2
    builders, failed = set(), 0
    for u in parse_units(path.read_text(encoding="utf-8")):
        d = choose(root, u["needs"], u["data_level"])
        save(root, f"unit:{u['id']}", d)
        if d["chosen"]:
            builders.add(d["chosen"]["agent"])
            print(f"{u['id']}: {d['chosen']['agent']} ({d['chosen']['model']}) for {', '.join(u['needs'])} on {u['data_level']} data")
        else:
            failed += 1
            print(f"{u['id']}: no eligible agent. {d['reason']}")
    data = load_json(root / "adlc/.state/routing.json", {}) or {}
    data["builders"] = sorted(builders)
    write_json(root / "adlc/.state/routing.json", data)
    audit("route.units", "build-orchestrate", None, {"builders": sorted(builders), "unrouted": failed})
    return 1 if failed else 0


def cmd_explain(args) -> int:
    root = repo_root()
    cat = load_json(root / "config/governance/agent_catalog.json")
    a = next((x for x in cat["agents"] if x["id"] == args.agent), None)
    if not a:
        print("Unknown agent.")
        return 2
    lv = levels(root)
    for phase, needs in cat["phase_needs"].items():
        ok, why = eligible(a, needs, args.data_level, lv, set())
        print(f"{phase:<18} {'yes' if ok else 'no '}  {why}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("phase"); p.add_argument("--phase", required=True); p.add_argument("--data-level", default="internal")
    u = sub.add_parser("units"); u.add_argument("--units", default="adlc/03-units.yaml")
    e = sub.add_parser("explain"); e.add_argument("--agent", required=True); e.add_argument("--data-level", default="internal")
    args = ap.parse_args()
    return {"phase": cmd_phase, "units": cmd_units, "explain": cmd_explain}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
