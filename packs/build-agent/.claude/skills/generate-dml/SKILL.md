---
name: generate-dml
description: >-
  Generate DML (transformation logic, INSERT/MERGE/UPDATE load scripts) for all in-scope tables, and reconcile lineage.json as the final step. Respects scope_selection. Use when the user asks to generate, create, write, or build the DML, load scripts, or transformation logic (typically after DDL).
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Generate DML

## Prerequisites
- `/plan-build` completed
- DDL artifacts in `state/run_id_<ID>/generated/ddl/` (artifact-writer validates column refs against these)
- `scope_selection.dml = true` in session.json (skip if false — print "DML was not selected in your scope. Skipping.")

## Required reads (supervisor — small files only)
- `session.json` — summary fields and `scope_selection` only
- `plans/table_index.json` — compact index (table names, waves, `estimated_dml_lines`, SCD2 flags, multi-source flags)
- `phase_handoff.json` from prior phase

**The supervisor MUST NOT read `canonical_build_model.json`, `source_column_registry.json`, `derivation_catalog.json`, `effective_conventions.json`, or DDL files directly.** All are passed as file paths in the delegation prompt. The `table_index.json` provides `estimated_dml_lines`, `has_scd2`, `has_multi_source` per table — this is all the supervisor needs for pre-sizing. Column-reference validation runs inside the artifact-writer against the DDL files it reads from disk.

## Delegation

**Mandatory when > 5 tables.** Delegate wave-by-wave using `artifact-writer` sub-agent (DML only mode).

## Goal

Generate load scripts for all tables. All heavy file reads (canonical model, source registry, derivation catalog, DDL artifacts) happen inside artifact-writer sub-agents — never in the supervisor window.

## Step 1 — Scope check and prepare

- Read `scope_selection` from session.json — if `dml = false`, print skip message and exit
- Read `table_index.json` for wave assignments, `estimated_dml_lines`, `has_scd2`, `has_multi_source` per table
- Verify DDL artifacts exist for this run's tables: `Bash(ls state/run_id_<ID>/generated/ddl/ | wc -l)` — confirm count matches table count. If DDL is missing for a table, note it — the artifact-writer will mark that table's DML with `[INSUFFICIENT INPUT]` for column references
- Create output subfolder: `state/run_id_<ID>/generated/dml/`

## Step 2 — Pre-size from table_index (no large-file reads needed)

Use `estimated_dml_lines` from `table_index.json`. Apply adjustment factors from the index flags:
- `has_scd2 = true`: multiply estimated lines by 1.4 (expire + insert version logic)
- `has_multi_source = true`: multiply by 1.3 (UNION/JOIN complexity)

Apply routing per delegation_protocol.md thresholds (single Write / section-streaming / part-file).

Write routing decisions to `state/run_id_<ID>/generated/_validation/prevalidation_dml.json` (DML family owns this file — separate from `prevalidation_ddl.json`).

## Step 3 — Generate DML wave by wave

Waves are sequential (dependency order). Within a wave, tables are independent and CAN run in parallel.

For each wave, spawn `artifact-writer` (DML-only mode). Delegation prompt includes:
- Artifact family: `dml`
- File paths (not contents): canonical_build_model, source_column_registry, derivation_catalog, effective_conventions, plans for this wave's tables, DDL files for this wave's tables (for column ref validation)
- Pre-sized write strategy per table
- Output path: `state/run_id_<ID>/generated/dml/`

Cache-warming: if wave has 3+ tables, launch first alone, wait for first tool result, then launch rest in parallel.

After each wave: validate via Bash only — `test -f` and `wc -c` per output file. Do NOT read DML content into supervisor.

**After each wave completes**: read the artifact-writer handoff. Extract `corrections_made[]` from the handoff. Append each correction entry to `prevalidation_dml.json` under `"dml_corrections"`. If handoff has no `corrections_made` key or it is empty, nothing to append.

## Step 4 — Lineage reconciliation

This step runs after ALL waves complete, before sync. It is a supervisor-level operation — no sub-agent needed.

**Skip condition**: if `planning_summary.lineage_generated = false` (lineage was not built at plan-build time), set `planning_summary.lineage_reconciled = true` and skip to Step 5. Also skip if both `scope_selection.pipeline = false` AND `scope_selection.tests = false` (no downstream consumer).

**Procedure:**
1. Read `state/run_id_<ID>/generated/_validation/prevalidation_dml.json`. Check `dml_corrections[]`.
2. If `dml_corrections` is empty or absent: set `session.json → planning_summary.lineage_reconciled = true`, set `generation_summary.lineage_reconciled = true`. Log "Lineage reconciliation: no corrections — planned lineage confirmed." to `logs.md`. Skip to Step 5.
3. If corrections exist: read `state/run_id_<ID>/plans/lineage.json`. For each correction entry:
   - Find the matching entry: `lineage.tables[]` where `table_id = correction.table_id`, then `column_lineage[]` where `target_column = correction.column`.
   - Update fields based on `correction_type`:
     - `source_column_renamed`: update `source_tables[].source_column` in that column entry
     - `transformation_changed`: update `transformation` field
     - `column_insufficient`: update `transformation` to correction's `actual_transformation`; set `confidence: "low"`; set `lineage_type: "assumption"`
     - `column_assumption`: set `lineage_type: "assumption"`; update `transformation`
   - Set `lineage_source: "reconciled"` on patched column entries.
   - If `correction.confidence_impact = "major"`: set column-level `confidence: "low"`.
4. Update `lineage.generated_at` to current timestamp. Write patched `lineage.json` back.
5. Set `session.json → planning_summary.lineage_reconciled = true`, `generation_summary.lineage_reconciled = true`.
6. Log count of patched columns to `logs.md`: "Lineage reconciliation: N columns patched across M tables."

## Step 5 — Sync and checkpoint

Sync to `outputs/`. Update `session.json` (`generation_summary.dml_complete = true`). Write `phase_handoff.json`.

Present to user: tables generated, unresolved column references (from handoff summaries), assumption count, lineage reconciliation result (N corrections applied or "confirmed — no corrections"). Recommend next generate command or `/evaluate-build`.

## Jira traceability

Follow the canonical traceability protocol in `.claude/skills/build-agent/references/jira_integration.md#traceability-protocol`. Phase summary line for this skill:

> `DML generation complete. <N> transformation scripts. Lineage corrections applied: <count or "none">.`

## Required writes
- `state/run_id_<ID>/generated/dml/<table_name>_dml.sql` (written by sub-agents)
- `state/run_id_<ID>/generated/_validation/prevalidation_dml.json` (supervisor writes corrections ledger)
- `state/run_id_<ID>/plans/lineage.json` (patched in-place if corrections exist)
- `state/run_id_<ID>/phase_handoff.json`
- `state/run_id_<ID>/session.json`
- Synced copies in `outputs/`
