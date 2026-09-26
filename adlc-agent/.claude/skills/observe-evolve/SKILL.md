---
name: observe-evolve
description: >-
  Phase 06. Learn from real usage: telemetry (logs, metrics, traces), anomaly and drift detection,
  cost, latency and performance monitoring, incident detection with runbook recommendations, user
  feedback and business outcome tracking. Produces the Improvement Backlog that feeds the next
  intent. Ends with gate G6 from a product owner.
argument-hint: "[optional: observation window, e.g. 14d]"
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
  - Agent
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(python3:*)
  - Bash(ls:*)
  - Bash(mkdir:*)
  - mcp__atlassian__*
  - mcp__github__*
---

# 06 Observe & Evolve

Purpose: produce `adlc/06-backlog.md`, which measures the release against the AIPRS success criteria and turns what was learned into prioritised backlog items. The one the product owner marks as the next intent starts the next cycle at /discover-define.

## Required Reads
- CLAUDE.md, config/project_config.json, .claude/skills/adlc/SKILL.md
- adlc/01-aiprs.md (success criteria), adlc/05-release.md (release ID, observation window)
- .claude/skills/adlc/templates/06-backlog.template.md

## Entry gate
`adlc_gate.py check --gate G5` must exit 0.

## Rules
- Telemetry is read through approved observability tools only, as aggregates. Never copy raw production records, prompts containing customer data, or user identifiers into the backlog.
- Compare outcomes to AIPRS success criteria by ID (`SC-`), with the measured value, the target, and the window.
- Every backlog item (`BL-`) has a `Trace:` to the observation (`OBS-`) and to the requirement it affects, an impact estimate, and a suggested phase to re-enter (01 for new intent, 02 for design, 03 for a defect).
- Mark at most one item `next_intent: true`; the product owner confirms it at G6.
- Promote reusable operational learnings to `memory/` per `memory/README.md` promotion rules. No client data.

## Idempotent re-entry
- Backlog exists for the current observation window and validation passes → skip to Human Gate.

## Steps
1. `state.py start --phase observe-evolve`.
2. Observation window and data sources: what was measured, from where, over which dates.
3. Outcome vs success criteria table.
4. Incidents and drift: anomalies, drift, cost or latency regressions, incidents, runbook actions taken.
5. User feedback and business outcome signals, summarised without personal data.
6. Backlog: prioritised `BL-` items; optionally create Jira issues via the Atlassian MCP server.
7. Next intent: the proposed item and why.
8. `validate_artifact.py --phase observe-evolve`, then `policy_check.py --phase observe-evolve`.
9. Run `metrics.py show` and include the run's delivery metrics in the summary. If the project has opted in (`config/project_config.json > telemetry.push`), send them with `metrics.py push`; the payload is numbers and IDs only.

## Human Gate G6
- Approver: the **product owner** team, via CODEOWNERS for `adlc/06-backlog.md`. The author cannot approve (GitHub blocks self-approval).
- Request (github mode): `python3 .claude/skills/adlc/scripts/gate_github.py request --gate G6 --intent <intent id>`. This opens a pull request labelled `adlc-gate-G6`.
- The approver reviews the pull request and approves it; merging passes the gate. Any later change to the artifact needs a new pull request and a new approval.
- Local mode: `adlc_gate.py request --gate G6 --summary "..."`, and the approver runs `/approve-gate G6`.

## Phase completion
10. `state.py complete --phase observe-evolve`.
11. Summary: success criteria met and missed, top incidents, backlog size, cycle metrics, proposed next intent, links.

## End Of Turn
G6 is waiting for a product owner in the gate pull request; give its link. Once approved, recommend `/discover-define` with the next intent. Stop.

Additional context from user invocation: $ARGUMENTS
