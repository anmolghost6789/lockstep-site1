# CHANGE IMPACT ROUTING

## Purpose

Changes arrive at any point: a reviewer rejects a gate, a stakeholder changes a requirement, evaluation fails, or production shows drift. Route each change to the earliest phase that owns the decision, then re-run every later phase whose approved artifact depends on it.

## Collect changes in one batch

Ask for the complete list of changes at once. Several small changes can add up to a deeper route-back.

## Routing matrix

| Change | Examples | Re-enter at | Then re-run |
|---|---|---|---|
| Wording or formatting in an artifact | typo, clearer phrasing, table layout, no change in meaning | the same phase | re-request that phase's gate only |
| Requirement or success criterion | new user story, changed NFR threshold, new risk, different target | /discover-define | 02 → 06 as affected |
| Design decision | new unit, different agent topology, model change, new tool or MCP server, RAG design | /architect-design | 03 → 06 as affected |
| Defect in built work | failing test, wrong behaviour, missing guardrail | /build-orchestrate | 04, then 05 if releasing |
| Evaluation setup | dataset, case count, metric definition (not the threshold) | /evaluate-validate | 05 if releasing |
| Release configuration | rollout %, flags, runbook, rollback trigger | /release-operate | 06 after the observation window |
| Production learning | incident, drift, cost or latency regression | /observe-evolve | next intent at /discover-define |

A threshold is a requirement. Changing it always goes back to /discover-define, never to /evaluate-validate.

## Gates reset downstream

Changing an approved artifact invalidates its gate. Every later phase that was approved on top of it must re-request its own gate after being re-run. Never carry an approval forward to changed work.

## Consistency

Keep IDs stable. A changed requirement keeps its ID and changes its text; a removed one is marked withdrawn rather than deleted, so trace links stay resolvable.

## Recording and routing a change

`python3 .claude/skills/adlc/scripts/recover.py change --type <wording|requirement|design|defect|eval_setup|release|production> --summary "…" --ids FR-002` applies the matrix above: it marks the re-entry phase and every later completed phase stale, voids their gates in local mode, refreshes `progress.json`, and writes the audit entry.

## Change log

Record each change in `adlc/.state/changes.jsonl`: change ID, the requester's words, classification, phase re-entered, affected IDs, artifacts updated, gates re-requested, and validation results.
