---
name: plan-build
description: >-
  Build dependency waves and evidence-aware per-table plans for ALL tables, and write lineage.json. No mid-phase approval; low-confidence plans are marked with notices. Use when the user wants to plan the build — dependency waves, per-table plans, or lineage — after input analysis.
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Plan Build

## Prerequisites
- `/analyze-inputs` completed
- Canonical model and conventions exist on disk

## Required reads (supervisor — small files only)
- `references/lineage_schema.md` — if `scope_selection.pipeline = true` OR `scope_selection.tests = true`
- `session.json` — summary fields only
- `phase_handoff.json` from prior phase

**The supervisor MUST NOT read `canonical_build_model.json`, `source_column_registry.json`, or `derivation_catalog.json` directly.** These are large files (100–500 KB on moderate runs) that belong in the sub-agent context window. The supervisor reads only the compact `table_index.json` and `build_blueprint.json` that the sub-agent produces.

## Delegation thresholds

**Delegate to `plan-generator` sub-agent when ANY of these are true:**
- Total table count > 20 (read from `phase_handoff.json::analysis_summary.table_count`)
- Complexity = `high` in session.json
- Any wave ordering ambiguity was flagged in the analysis handoff

**Below all thresholds:** supervisor may plan inline, but must still apply the context discipline rule — read only the per-table slice needed at a time, not the full canonical model.

## Goal

Translate discovery into a build blueprint. Supervisor receives only the compact index and blueprint; all heavy JSON reading happens in the sub-agent (or inline with strict discipline).

## Step 1 — Decide delegation path

Read `phase_handoff.json` to get table count and complexity. Check delegation thresholds.

**Path A — delegate (above thresholds):**

Build the delegation prompt with:
- Paths to discovery artifacts (canonical_build_model, relationships, effective_conventions, dq_catalog)
- Output paths for plans directory, table_index.json, build_blueprint.json
- `scope_selection` from session.json (sub-agent plans only selected artifact families)
- Any user wave assignment or ordering constraints from session.json decisions

Spawn `plan-generator` sub-agent. Supervisor holds only session summary while it runs.

After handoff: validate outputs exist on disk. Read ONLY `table_index.json` and `build_blueprint.json` — both compact. Do not read individual `<table>_plan.json` files.

**Path B — inline (below all thresholds, ≤ 20 tables):**

Apply planning steps inline, reading the canonical model one table at a time. Write per-table plan files as you go. Write `table_index.json` (compact) and `build_blueprint.json` at the end.

## Step 2 — Validate handoff outputs

After delegation (or inline):
- Confirm `table_index.json` exists and is non-empty (`wc -c`)
- Confirm `build_blueprint.json` exists and is non-empty
- Confirm the number of `<table>_plan.json` files matches `table_index.json::total_tables`
- Do NOT read individual plan files to verify their contents — trust the sub-agent's handoff

If counts don't match, re-delegate for the missing tables.

## Step 3 — Verify lineage.json written by plan-generator

**Skip this step if both `scope_selection.pipeline = false` AND `scope_selection.tests = false`.** Log skip to `logs.md` and proceed to Step 4.

Otherwise, the `plan-generator` sub-agent already wrote `lineage.json` as its final output (see plan-generator agent definition). The supervisor does NOT read plan files or domain_context.md to re-assemble lineage — that work happened inside the sub-agent which already had the canonical model, relationships, and domain context in its window.

**Supervisor verification (filesystem check only):**
```bash
test -f state/run_id_<ID>/plans/lineage.json && wc -c state/run_id_<ID>/plans/lineage.json
```

If absent: re-delegate to plan-generator with explicit instruction to write lineage.json. Do not attempt to assemble lineage.json in the supervisor context.

If present and non-empty: proceed to Step 4.

**Why this changed:** assembling lineage.json in the supervisor required reading all 22+ per-table plan files plus domain_context.md — adding ~9 minutes and violating the supervisor context budget rule. The plan-generator has all required data (canonical model, relationships, domain_context) already in its window and can write lineage.json as its last output step with zero additional file reads.

## Step 4 — Sync and checkpoint

Sync all plans and lineage.json to `outputs/`. Update session.json:
- Record table count, wave count, artifact family counts from `build_blueprint.json`
- Set `planning_summary.lineage_generated: true` (or `false` if Step 3 was skipped)
- Set `planning_summary.lineage_reconciled: false`

Write `phase_handoff.json`.

Present to user from `build_blueprint.json` only — do not re-read plan files:
- Wave summary (wave N: X tables)
- Total artifact counts per family
- Low-confidence table count
- Any circular dependency or wave violation findings
- Lineage: "lineage.json written — N tables, M edges, P external sources" (or "lineage skipped — pipeline and tests not in scope")

Recommend: `/generate-ddl` as the next step (DDL is always first; user invokes it manually).

Tell user: "Run `/compact focus on: run_id, phase status, user decisions, next steps` then run `/generate-ddl`."

## STOP gate — mandatory

After writing `phase_handoff.json` and presenting the recommendation, you MUST stop the turn. Do NOT:

- invoke `/generate-ddl`, `/generate-dml`, `/generate-dq`, `/generate-pipeline`, `/generate-tests`, or any sub-agent for those phases
- spawn `artifact-writer` for any artifact family
- write any file under `state/run_id_<ID>/generated/`
- continue producing artifacts beyond the plan

The user invokes the next command manually. If the user has asked you to "do everything" or chain phases together, refuse — explain that human-in-the-loop review between phases is required and they should run `/generate-ddl` next.

## Jira traceability

Follow the canonical traceability protocol in `.claude/skills/build-agent/references/jira_integration.md#traceability-protocol`. Phase summary line for this skill:

> `Build plan complete. <N> tables across <W> waves. Dependency graph written.`

## Required writes
- `state/run_id_<ID>/plans/table_index.json`
- `state/run_id_<ID>/plans/build_blueprint.json`
- `state/run_id_<ID>/plans/<table_name>_plan.json` (one per table — written by sub-agent or inline)
- `state/run_id_<ID>/plans/lineage.json` (if scope_selection.pipeline = true OR tests = true)
- `state/run_id_<ID>/phase_handoff.json`
- `state/run_id_<ID>/session.json`
- Synced copies in `outputs/`
