#!/usr/bin/env python3
"""Pull-request gates for gate_mode = github. Requires git and an authenticated GitHub CLI (gh).

  gate_github.py request --gate G2 --intent INT-0192   branch, commit the artifact, open a labelled pull request
  gate_github.py check   --gate G1                     exit 0 only if the gate PR was approved and merged,
                                                       and the artifact on the default branch is unchanged since
  gate_github.py status                                one line per gate

Exit codes for check: 0 approved, 2 no merged gate PR, 4 artifact changed after merge, 7 gh or git unavailable.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

from _common import load_json, phase_by_gate, repo_root
from audit_log import append as audit


def run(*cmd: str, check: bool = True) -> str:
    out = subprocess.run(cmd, capture_output=True, text=True)
    if check and out.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:3])} failed: {out.stderr.strip() or out.stdout.strip()}")
    return out.stdout.strip()


def settings(root):
    cfg = load_json(root / "config/project_config.json")
    gh = cfg.get("github", {})
    return gh.get("default_branch", "main"), gh.get("branch_prefix", "adlc/"), gh.get("gate_label_prefix", "adlc-gate-")


def require_tools() -> bool:
    if not shutil.which("git") or not shutil.which("gh"):
        print("GitHub mode needs git and the GitHub CLI (gh), signed in with `gh auth login`. Or set gate_mode to local.")
        return False
    return True


def cmd_request(args) -> int:
    root = repo_root()
    if not require_tools():
        return 7
    base, prefix, label = settings(root)
    phase = phase_by_gate(root, args.gate)
    branch = f"{prefix}{args.intent}/{phase['number']}-{phase['id']}"
    run("git", "switch", "-C", branch)
    run("git", "add", phase["artifact"], "adlc/.state")
    if phase["id"] == "architect-design":
        run("git", "add", "adlc/adr", check=False)
    run("git", "commit", "-m", f"ADLC {args.gate}: {phase['label']} for {args.intent}", check=False)
    run("git", "push", "-u", "origin", branch)
    run("gh", "label", "create", f"{label}{args.gate}", "--force", "--description", f"ADLC gate {args.gate}", check=False)
    packet = root / f"adlc/.state/context_packets/{phase['number']}-{phase['id']}.md"
    body = packet.read_text(encoding="utf-8") if packet.exists() else f"ADLC {args.gate}: {phase['label']}."
    extra: list[str] = []
    roles = load_json(root / "config/governance/gate_roles.json")
    for role in roles["gates"][args.gate].get("additional_roles_if_risk", {}).get(args.risk or "", []):
        team = roles.get("github_teams", {}).get(role, "")
        if team:
            extra += ["--reviewer", team.lstrip("@")]
    url = run("gh", "pr", "create", "--base", base, "--head", branch, "--label", f"{label}{args.gate}",
              "--title", f"ADLC {args.gate}: {phase['label']} ({args.intent})", "--body", body, *extra)
    audit("gate.requested", phase["id"], args.gate, {"mode": "github", "pull_request": url})
    print(f"{args.gate} requested: {url}\nCODEOWNERS routes it to the approver team; branch protection blocks the merge until they approve.")
    return 0


def merged_gate_pr(gate: str, label: str):
    raw = run("gh", "pr", "list", "--state", "merged", "--label", f"{label}{gate}", "--limit", "1",
              "--json", "number,url,mergedAt,mergeCommit,reviewDecision")
    items = json.loads(raw or "[]")
    return items[0] if items else None


def cmd_check(args) -> int:
    root = repo_root()
    if not require_tools():
        return 7
    base, _, label = settings(root)
    phase = phase_by_gate(root, args.gate)
    pr = merged_gate_pr(args.gate, label)
    if not pr:
        print(f"{args.gate} ({phase['label']}) has no merged, approved gate pull request yet.")
        return 2
    if pr.get("reviewDecision") not in ("APPROVED", None):
        print(f"{args.gate} pull request {pr['url']} was merged without an approving review ({pr.get('reviewDecision')}). Check branch protection.")
        return 2
    run("git", "fetch", "origin", base, check=False)
    merge_sha = (pr.get("mergeCommit") or {}).get("oid")
    if merge_sha:
        changed = subprocess.run(["git", "diff", "--quiet", merge_sha, f"origin/{base}", "--", phase["artifact"]]).returncode
        if changed:
            print(f"{phase['artifact']} changed on {base} after {args.gate} was approved in {pr['url']}. Re-run {phase['id']} and request the gate again.")
            return 4
    print(f"{args.gate} approved and merged: {pr['url']}")
    return 0


def cmd_status(_args) -> int:
    root = repo_root()
    if not require_tools():
        return 7
    _, _, label = settings(root)
    for gate in load_json(root / "config/governance/gate_roles.json")["gates"]:
        pr = merged_gate_pr(gate, label)
        if pr:
            print(f"{gate}  approved  {pr['url']}")
            continue
        open_raw = run("gh", "pr", "list", "--state", "open", "--label", f"{label}{gate}", "--limit", "1", "--json", "url")
        items = json.loads(open_raw or "[]")
        print(f"{gate}  pending   {items[0]['url']}" if items else f"{gate}  not requested")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("request")
    r.add_argument("--gate", required=True)
    r.add_argument("--intent", required=True)
    r.add_argument("--risk", choices=["low", "medium", "high", "critical"])
    c = sub.add_parser("check")
    c.add_argument("--gate", required=True)
    sub.add_parser("status")
    args = ap.parse_args()
    try:
        return {"request": cmd_request, "check": cmd_check, "status": cmd_status}[args.cmd](args)
    except RuntimeError as e:
        print(str(e))
        return 7


if __name__ == "__main__":
    sys.exit(main())
