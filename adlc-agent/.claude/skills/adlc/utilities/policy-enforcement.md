# Policy Enforcement

Policy runs in three places. Each catches what the others cannot.

| Layer | When | Mechanism | Blocks |
|---|---|---|---|
| Runtime | Every tool call | `.claude/hooks/pre_tool_guard.py` | Writes to gate/audit folders, secrets in content, writes outside the repo, non-allow-listed MCP servers or tools, MCP servers outside their permitted phases |
| Phase | Before every gate request | `scripts/policy_check.py --phase <id>` | The gate request, until every check passes |
| Pipeline | Before production deploy | CI runs the G5 check (`gate_github.py check --gate G5`, or `adlc_gate.py` in local mode) | The deploy, if G5 is not approved for the exact release artifact |

## External evidence

Checks marked `external` in `specs/policy_contract.yaml` (license scan, SBOM) are run by your CI tools, not by the agent. CI writes `adlc/.state/evidence/<check>.json`. The agent cannot mark these as passed; it can only wait for evidence.

## When a check fails

Fix the cause and re-run. Do not edit the policy report. If a check cannot pass for a legitimate reason, the phase may request its gate only after a `waiver_approver` records a waiver, which is logged and expires.
