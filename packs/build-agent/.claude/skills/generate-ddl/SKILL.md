---
name: generate-ddl
description: >-
  Generate DDL (CREATE TABLE statements) for all in-scope tables. Respects scope_selection from session.json. Use when the user asks to generate, create, write, or build the DDL or CREATE TABLE statements.
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Generate DDL

## Prerequisites
- `/plan-build` completed
- `scope_selection.ddl = true` in session.json (skip this command entirely if false — print "DDL was not selected in your scope. Skipping.")

## Required reads (supervisor — small files only)
- `session.json` — summary fields and `scope_selection` only
- `plans/table_index.json` — compact index (table names, waves, estimated line counts)
- `phase_handoff.json` from prior phase

**The supervisor MUST NOT read `canonical_build_model.json`, `effective_conventions.json`, or any plan file directly.** These are passed as file paths in the delegation prompt. The artifact-writer sub-agent reads them. The `table_index.json` provides the estimated line counts the supervisor needs for pre-sizing — no other large file is required.

## Delegation

**Mandatory when > 5 tables.** Delegate wave-by-wave using `artifact-writer` sub-agent (DDL only mode).

## Goal

Generate DDL for all tables. Supervisor orchestrates; sub-agents do all heavy file reads and writes.

## Step 1 — Scope check and prepare

- Read `scope_selection` from session.json — if `ddl = false`, print skip message and exit
- Read `table_index.json` for wave assignments and `estimated_ddl_lines` per table
- Create output subfolder: `state/run_id_<ID>/generated/ddl/`

## Step 2 — Pre-size from table_index (no large-file reads needed)

The `table_index.json::waves[].tables[].estimated_ddl_lines` field (written by `plan-generator`) already contains the pre-sizing data. Use it directly:

- estimated DDL lines × ~50 bytes/line = estimated KB
- Apply routing: ≤ 30 KB → single Write, 30–50 KB → section-streaming, > 50 KB → part-file

Write routing decisions to `state/run_id_<ID>/generated/_validation/prevalidation_ddl.json` (DDL family owns this file — no appending to a shared file).

## Step 3 — Generate DDL wave by wave

For each wave, spawn `artifact-writer` (DDL-only mode). Delegation prompt includes:
- Artifact family: `ddl`
- File paths (not contents): canonical_build_model, effective_conventions, plans for this wave's tables
- Pre-sized write strategy per table from Step 2
- Output path: `state/run_id_<ID>/generated/ddl/`

Cache-warming: if wave has 3+ tables, launch first table's agent alone, wait for first tool result, then launch remaining in parallel.

After each wave completes, validate via Bash (`test -f`, `wc -c`) — do NOT read DDL content into supervisor context.

## Step 4 — Sync and checkpoint

Sync to `outputs/`. Update `session.json` (`generation_summary.ddl_complete = true`, table count). Write `phase_handoff.json`.

Present to user: tables generated, any validation failures (file missing or zero bytes), assumption count from handoff summaries. Recommend next generate command or `/evaluate-build`.

## Jira traceability

Follow the canonical traceability protocol in `.claude/skills/build-agent/references/jira_integration.md#traceability-protocol`. Phase summary line for this skill:

> `DDL generation complete. <N> CREATE TABLE statements. Tables: <first 10 then "and <K> more">.`

## Required writes
- `state/run_id_<ID>/generated/ddl/<table_name>_ddl.sql` (written by sub-agents)
- `state/run_id_<ID>/generated/_validation/prevalidation_ddl.json` (supervisor writes this)
- `state/run_id_<ID>/phase_handoff.json`
- `state/run_id_<ID>/session.json`
- Synced copies in `outputs/`
