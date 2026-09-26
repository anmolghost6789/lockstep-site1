---
name: generate-dq
description: >-
  Generate data-quality check scripts for all in-scope tables, in the format set by the dq_framework convention. Respects scope_selection. Use when the user asks to generate, create, write, or build the DQ / data-quality checks.
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Generate DQ

## Prerequisites
- `/plan-build` completed
- DDL artifacts in `state/run_id_<ID>/generated/ddl/` (artifact-writer validates column refs against these)
- `scope_selection.dq = true` in session.json (skip if false — print "DQ checks were not selected in your scope. Skipping.")

## Required reads (supervisor — small files only)
- `session.json` — summary fields, `scope_selection`, and `dq_framework` convention (read from session.json if recorded there, else read only the `dq_framework` field from `effective_conventions.json`)
- `plans/table_index.json` — compact index
- `phase_handoff.json` from prior phase

**The supervisor reads ONLY `dq_framework` from `effective_conventions.json`** — a single scalar field. It does NOT read the full file. All other discovery artifacts (canonical model, dq_catalog, DDL files) are passed as file paths to artifact-writer.

## Delegation

**Mandatory when > 5 tables.** Delegate wave-by-wave using `artifact-writer` sub-agent (DQ only mode).

## Goal

Generate DQ check scripts for all tables. All heavy file reads happen inside sub-agents.

## Step 1 — Scope check and read dq_framework

- Read `scope_selection` from session.json — if `dq = false`, print skip message and exit
- Read `dq_framework` from session.json or (if not cached there) read only that field from `effective_conventions.json`
- For `custom` framework: confirm the emission format with the user now (the one permitted mid-phase interaction for this case)
- Verify DDL artifacts exist: `Bash(ls state/run_id_<ID>/generated/ddl/ | wc -l)`
- Create output subfolder: `state/run_id_<ID>/generated/dq/`

## Step 2 — Pre-size (DQ files are compact)

DQ artifacts are typically 2–8 KB per table (sql_procedural), up to 15–20 KB for tables with > 30 complex rules or Great Expectations suites. Use `table_index.json` rule counts if available; otherwise default to single Write for all tables. Write pre-sizing to `state/run_id_<ID>/generated/_validation/prevalidation_dq.json` (DQ family owns this file — separate from prevalidation_ddl and prevalidation_dml).

## Step 3 — Generate DQ wave by wave

DQ generation is **independent of DML generation** — both depend only on DDL. The user runs `/generate-dml` and `/generate-dq` separately for human-in-the-loop review; either can be invoked first after `/generate-ddl` completes.

For each wave, spawn `artifact-writer` (DQ-only mode). Delegation prompt includes:
- Artifact family: `dq`
- `dq_framework` value (single scalar — already read in Step 1)
- File paths (not contents): canonical_build_model, dq_catalog, effective_conventions, plans for this wave's tables, DDL files for this wave's tables (for column ref validation)
- Output path: `state/run_id_<ID>/generated/dq/`

After each wave: validate via `test -f` and `wc -c` only. Do NOT read DQ content into supervisor.

## Step 4 — Sync and checkpoint

Sync to `outputs/`. Update `session.json` (`generation_summary.dq_complete = true`). Write `phase_handoff.json`.

Present to user: tables generated, stub count (tables with no DQ rules), framework used, assumption count.
Recommend next generate command or `/evaluate-build`.

## Jira traceability

Follow the canonical traceability protocol in `.claude/skills/build-agent/references/jira_integration.md#traceability-protocol`. Phase summary line for this skill:

> `DQ generation complete. <N> check scripts across <M> tables. Framework: <dq_framework>.`

## Required writes
- `state/run_id_<ID>/generated/dq/<table_name>_dq.<ext>` (written by sub-agents)
- `state/run_id_<ID>/generated/_validation/prevalidation_dq.json` (supervisor writes this)
- `state/run_id_<ID>/phase_handoff.json`
- `state/run_id_<ID>/session.json`
- Synced copies in `outputs/`
