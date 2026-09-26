---
name: evaluate-build
description: >-
  Re-read generated artifacts from disk, score them deterministically, and classify remediation. Always delegated to the build-evaluator sub-agent. Use when the user wants to evaluate, score, QA, assess, or check the quality/readiness of the generated build artifacts.
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Evaluate Build

## Prerequisites
- All selected `/generate-<artifact>` commands completed (`/generate-ddl`, `/generate-dml`, `/generate-dq`, `/generate-pipeline`, `/generate-tests` per `scope_selection`)

## Required reads
- `references/evaluation_rubric.md`
- `references/remediation_and_packaging.md`
- `session.json`
- discovery artifacts, plans, generated outputs from disk
- `plans/lineage.json` — path check and delegate read (for faithfulness checklist item 10)
- `phase_handoff.json` from prior phase

## Delegation

**Always delegated.** Spawn `build-evaluator` sub-agent. Evaluation reads ALL generated artifacts — always isolate it.

## Goal

Produce deterministic quality assessment and remediation list.

## Step 1 — Inventory actual artifacts from disk

Verify what exists. Trust filesystem over state. Include pipeline artifacts (`generated/pipeline/`), `tests_data/`, `tests_pipeline/`, and `plans/lineage.json` in the inventory — these are new artifact families in addition to DDL/DML/DQ/tests.

## Step 2 — Write input quality disclosure

State: missing inputs, inferences, assumptions, resolved bugs/contradictions.

## Step 2a — Execute faithfulness checklist

From evaluation_rubric.md: join types, unknown-member SK, RECORD_HASH order, derivation rules, scope compliance, instruction deviations, source column references, DDL completeness, DQ syntax, and (conditional) lineage consistency check (item 10 — see evaluation_rubric.md for full spec). Pass `plans/lineage.json` path to build-evaluator for item 10.

## Step 3 — Score dimensions

Use exact weights from evaluation_rubric.md. Each dimension 0-10 with evidence from disk.

## Step 4 — Apply gate and write remediation

Classify: passed, passed_with_actions, failed. Write concrete remediation items.

## Step 5 — Sync and checkpoint

Write evaluation outputs. Sync. Update session.json. Write phase_handoff.json.

Present to user: overall score, gate result, top remediation items. Recommend: `/revise-build` if remediation items remain, otherwise the run is complete — run `/inspect-build` for a status summary.

Tell user: "Run `/compact focus on: run_id, phase status, user decisions, next steps` then run the recommended command."

## Jira traceability

Follow the canonical traceability protocol in `.claude/skills/build-agent/references/jira_integration.md#traceability-protocol`. Phase summary line for this skill:

> `Build evaluation complete. Score: <overall>. <N> remediation items. Quality gate: <verdict>.`

After posting, if `inputs/additional_documents/jira_issue_mapping.json` exists, recommend `/publish-build-summary` as the next step. If absent, the run is complete.

## Required writes
- `state/run_id_<ID>/evaluation/`
- `state/run_id_<ID>/phase_handoff.json`
- `state/run_id_<ID>/session.json`
- Synced copies in `outputs/`
