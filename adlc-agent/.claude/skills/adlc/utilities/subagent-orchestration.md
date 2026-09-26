# Subagent Orchestration

The orchestrator (main conversation) owns state, human communication, gate requests and final decisions. Subagents do bounded work and return a short summary plus file paths.

| Subagent | Phase | Spawn when | Writes | Never |
|---|---|---|---|---|
| requirements-analyst | 01 | inputs > 15 files or > 15 MB | adlc/.state/index/inputs.json | asks humans, writes the AIPRS |
| solution-architect | 02 | > 8 units or > 2 systems of record | draft sections for the orchestrator to merge | edits config or ADR status |
| bolt-builder | 03 | > 3 independent units | code in its unit's file scope; bolt records | touches another unit's files |
| adlc-evaluator | 04 | always | adlc/.state/eval/, scorecard draft | evaluates code it built |
| release-auditor | 05 | always | Readiness Checklist section | deploys anything |

Rules: subagents do not talk to each other, do not request or decide gates, and inherit the phase's MCP allow-list. Fan-out uses disjoint file scopes so no two subagents edit the same file.
