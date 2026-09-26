---
name: generate-tests
description: >-
  Generate data tests (SQL/dbt assertions per table) and pipeline tests (orchestration assertions); pipeline tests are skipped automatically if no pipeline artifacts exist. Respects scope_selection. Use when the user asks to generate, create, write, or build the tests — data tests and/or pipeline tests.
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Generate Tests

## Prerequisites
- `/plan-build` completed
- DDL artifacts in `state/run_id_<ID>/generated/ddl/` (artifact-writer validates column refs against these)
- `scope_selection.tests = true` in session.json (skip entirely if false — print "Test scripts were not selected in your scope. Skipping.")
- Pipeline artifacts in `generated/pipeline/` — required for pipeline test category only (not for data tests)

## Required reads (supervisor — small files only)
- `session.json` — summary fields, `scope_selection`, and `generation_summary` only
- `plans/table_index.json` — compact index (SCD2 flags, derivation rule counts, wave assignments)
- `phase_handoff.json` from prior phase

**The supervisor MUST NOT read `canonical_build_model.json`, `derivation_catalog.json`, `effective_conventions.json`, DDL files, DML files, or pipeline YAML files directly.** All passed as file paths in the delegation prompt.

## Delegation

**Mandatory when > 5 tables (data tests).** Delegate wave-by-wave using `artifact-writer` sub-agent.
**Pipeline tests**: delegate as a single pass to `artifact-writer` (pipeline-tests mode) — no wave splitting needed; pipeline tests operate on the entire pipeline artifact set.

## Goal

Generate both test categories in a single command invocation. Data tests verify the correctness of the generated SQL artifacts. Pipeline tests verify the correctness of the generated orchestration artifacts.

---

## Step 1 — Scope check and category determination

- Read `scope_selection` from session.json — if `tests = false`, print skip message and exit.
- Determine active categories:
  - **Data tests**: always active when tests = true.
  - **Pipeline tests**: active only if `generated/pipeline/` exists and is non-empty:
    ```bash
    ls state/run_id_<ID>/generated/pipeline/ 2>/dev/null | wc -l
    ```
    If 0 or absent: set `pipeline_tests_active = false`, note "Pipeline artifacts not found — pipeline test category will be skipped. Run `/generate-pipeline` first to enable pipeline tests."
    If > 0: set `pipeline_tests_active = true`. Also read `session.json → scope_selection.pipeline_platform` for format selection.

- Create output subfolders:
  ```bash
  mkdir -p state/run_id_<ID>/generated/tests_data/
  mkdir -p state/run_id_<ID>/generated/tests_pipeline/
  ```

---

## Step 2 — Pre-size data tests

Test files are typically 3–12 KB per table. Tables with `has_scd2 = true` may reach 15–20 KB. Tables with derivation rule count > 20 may reach 20–30 KB.

Routing:
- Default: single Write for all tables
- `has_scd2 = true` AND derivation rule count > 20: section-streaming

Write pre-sizing to `state/run_id_<ID>/generated/_validation/prevalidation_tests.json`.

---

## Step 3 — Generate data tests wave by wave

For each wave, spawn `artifact-writer` (data-tests mode). Delegation prompt includes:
- Artifact family: `data_tests`
- File paths (not contents): canonical_build_model, derivation_catalog, effective_conventions, per-table plans for this wave, DDL files for this wave
- DML file paths if they exist (artifact-writer reads only if present — for assertion targets)
- Output path: `state/run_id_<ID>/generated/tests_data/`
- Output naming: `<table_name>_data_tests.sql` (or `<table_name>_data_tests.yml` for dbt framework)

After each wave: validate via `test -f` and `wc -c` only. Do NOT read test content into supervisor.

The artifact-writer enforces the **Data test minimum matrix** (per-table, transformation-heavy, SCD2, incremental, and DQ-heavy assertions) — see `references/test_assertion_standards.md`.

---

## Step 4 — Generate pipeline tests (if pipeline_tests_active = true)

Delegate to `artifact-writer` (pipeline-tests mode) as a single pass. Delegation prompt includes:
- Artifact family: `pipeline_tests`
- `pipeline_platform`: value from `session.json → scope_selection.pipeline_platform`
- Path to `plans/lineage.json`
- Path to `generated/pipeline/` directory
- Path to `effective_conventions.json`
- Output path: `state/run_id_<ID>/generated/tests_pipeline/`

The artifact-writer enforces the **Pipeline test output format** (per platform) and the
**Pipeline test minimum matrix** (structural/completeness, operational/correctness, and
platform-specific checks for Databricks / Snowflake / Generic) — see
`references/test_assertion_standards.md`.

After delegation: validate via `test -f` and `wc -c` only.

---

## Step 5 — Sync and checkpoint

Sync both `tests_data/` and `tests_pipeline/` to `outputs/`.

Update session.json:
- `generation_summary.tests_data_complete = true`
- `generation_summary.tests_pipeline_complete = true` (or `false` if pipeline_tests_active = false)
- `generation_summary.tests_complete = true` (deprecated alias for tests_data_complete — kept for backward compat)

Write `phase_handoff.json`.

Present to user:
- Data tests: tables covered, SCD2 test count, FK integrity test count, stub count, assumption count
- Pipeline tests: checks generated (or "skipped — pipeline artifacts not found"), platform, format
- Validation status for both categories

Recommend: `/evaluate-build`.

Tell user: "Run `/compact focus on: run_id, phase status, user decisions, next steps` then run `/evaluate-build`."

## Jira traceability

Follow the canonical traceability protocol in `.claude/skills/build-agent/references/jira_integration.md#traceability-protocol`. Phase summary line for this skill:

> `Test generation complete. <D> data tests + <P> pipeline tests.`

## Required writes
- `state/run_id_<ID>/generated/tests_data/<table_name>_data_tests.sql` (written by sub-agents)
- `state/run_id_<ID>/generated/tests_pipeline/pipeline_tests.{py|sql|yml}` (written by sub-agent; only if pipeline_tests_active)
- `state/run_id_<ID>/generated/_validation/prevalidation_tests.json` (supervisor writes this)
- `state/run_id_<ID>/phase_handoff.json`
- `state/run_id_<ID>/session.json`
- Synced copies in `outputs/`
