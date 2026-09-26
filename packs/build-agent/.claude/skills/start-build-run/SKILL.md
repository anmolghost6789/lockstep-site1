---
name: start-build-run
description: >-
  Begin or resume a build run: inventory inputs, run structural and semantic checks, generate the Input Evaluation Report (pass/warn/error), and initialize run state. Use when the user wants to start, begin, kick off, initialize, or resume a build run, or asks to ingest or evaluate the build inputs before generating anything.
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Start Build Run

## Required reads
- `references/input_validation.md`
- existing files in `runs/_memory/`, if present
- existing run folders under `runs/run_id_*/`, if present

## Delegation awareness

This phase runs in the supervisor context (user interaction at the end).

## Goal

Establish new or existing run, check Python dependencies, ask the user which artifact types to generate, inventory inputs, run quality checks, generate the Input Evaluation Report with producible outputs matrix, and initialize the run ledger.

## Step -1 — Bootstrap Python dependencies

Before doing anything else, verify the required Python packages are available:

```bash
python -c "import openpyxl, pdfplumber, pypdf, mammoth, docx, chardet; print('All packages OK')" 2>&1
```

If the check fails, print this message and **halt**:

```
⚠️ Missing Python dependencies. Run the following command first, then re-run /start-build-run:

  pip install -r .claude/skills/build-agent/scripts/requirements.txt

Packages needed: openpyxl, xlrd, pdfplumber, pypdf, mammoth, python-docx, chardet
These are required to read .xlsx, .pdf, and .docx input files.
```

If the check passes, print `✅ Python dependencies OK` and continue.

## Step 0 — Scope selection

**This is the only mid-phase user question permitted in the entire workflow.** It is asked once at the very start of a new run, before any file scanning.

Present this menu to the user:

```
Which artifact types do you want to generate for this run?

  1. DDL       — CREATE TABLE statements, column definitions, audit columns
  2. DML       — transformation logic, load scripts (INSERT/MERGE/UPDATE)
  3. DQ        — data quality check scripts (SQL, dbt, Great Expectations, etc.)
  4. Pipeline  — orchestration YAML for Databricks Workflows, Snowflake Tasks, or Generic
  5. Tests     — data tests (SQL/dbt assertions) + pipeline tests (orchestration assertions)

Options:
  • Type numbers separated by commas to select specific types  (e.g. 1,2,3)
  • Press Enter with no input to generate ALL five (recommended)
  • Type "all" to generate all five

Your selection:
```

Map the response to a `scope_selection` object and lock it in `session.json`:

```json
{
  "scope_selection": {
    "ddl": true,
    "dml": true,
    "dq": true,
    "pipeline": true,
    "tests": true,
    "pipeline_platform": null,
    "locked_at": "ISO timestamp",
    "user_input": "all"
  }
}
```

**Auto-enable rule:** if the user selects `pipeline = true` but `dml = false`, print:
> "Pipeline generation requires DML (pipeline tasks orchestrate the DML transformations). DML has been automatically enabled."
Then set `dml: true` in `scope_selection`. Record this auto-enable in checkpoint history.

**Platform selection (when pipeline = true):** immediately after the user selects scope, if `pipeline = true`, ask:

```
Which deployment platform will this pipeline run on?

  1. Databricks   — Databricks Workflows (YAML job definition, tasks with depends_on)
  2. Snowflake    — Snowflake Tasks (SQL DAG with AFTER clauses, inline DML)
  3. Generic      — Platform-neutral YAML (map to Airflow, ADF, Prefect, or any orchestrator)

Your selection:
```

Map to `pipeline_platform`: `"databricks"` | `"snowflake"` | `"generic"`.
Lock immediately in `session.json::scope_selection.pipeline_platform`. Record as checkpoint decision.

**Rationale:** Asking early lets plan-build and generate-build use the platform value without a mid-phase question later. `/generate-pipeline` Step 2 checks if the value is already set and skips the question — no duplication.

If `pipeline = false`: set `pipeline_platform: null` and skip this prompt entirely.

If the user is **continuing** an existing run (not starting new), skip this step — the scope is already locked in `session.json`. Display it as a reminder:

```
Resuming run <run_id>. Scope locked: DDL ✅  DML ✅  DQ ✅  Pipeline ✅  Tests ✅
```

The `scope_selection` propagates to `/plan-build` (which plans only selected artifact families per table) and to each `/generate-*` command (which generates only its own family). The producible outputs matrix in the Input Evaluation Report reflects selected scope only.

## Step 1 — Decide new or continue

Ask the user: new run or continue?

If continuing:
- List available runs under `runs/run_id_*/`
- Read selected `session.json`
- If `active_phase` is `eval_complete` and user re-ran this command, offer re-evaluation
- Summarize current phase and recommended next action

If new:
- Create run id and folder structure per runtime contract

## Step 2 — Read memory

If `runs/_memory/` exists, read all files. Note active conventions and decisions.

## Step 3 — Inventory, classify, and evaluate inputs

### 3a. Inventory inputs

Read every file in `inputs/` and classify by content:
- sttm_or_mapping, data_model, dq_rules, enterprise_context, domain_context, project_context, user_instructions, business_rules, legacy_code, known_gaps, reference, unknown

### 3b. Detect template conformance

Check if inputs match golden template structure (STTM, Data Model, DQ Rules). Template conformance is a confidence accelerator, not a requirement.

### 3c. Run structural checks

Per `references/input_validation.md`: blockers, criticals, majors, minors. Evidence capture for every finding.

### 3d. Run semantic anomaly checks

Execute the semantic anomaly checklist. Generalized checks:
- Cross-document contradictions between any pair of input files
- Instruction vs best-practice conflicts
- Suspiciously empty gaps documents
- Wave ordering violations against dependency graph
- Annotated bugs/markers in input files
- Dangling references to entities not in mappings

Write `state/run_id_<ID>/discovery/semantic_checks.json`.

### 3e. Determine producible outputs

Based on input inventory, determine what the agent CAN produce:

| Output | Condition |
|---|---|
| DDL | Table/column definitions exist |
| DML | Source-to-target mappings exist |
| DQ checks | DQ rules exist in input |
| Test scripts | Test patterns or conventions exist |
| Deployment scripts | Deployment conventions exist |

For each: `full`, `partial`, or `not_possible`.

### 3f. Generate Input Evaluation Report

Compute: verdict (pass/warn/error), readiness_percent, complexity, findings, producible outputs matrix, recommendations, assumptions.

Write:
- `state/run_id_<ID>/discovery/input_evaluation_report.json`
- `state/run_id_<ID>/discovery/input_evaluation_report.md`

### 3g. Generate Execution Plan

Read `references/execution_plan.md` for the template and schema. Using data from Steps 3a-3f, generate the plan showing: table inventory by layer, phase plan with dependencies, wave preview, convention preview (naming, SCD2 marker, audit columns, DQ framework), known gaps carried from the evaluation report, and estimated effort.

Write:
- `state/run_id_<ID>/discovery/execution_plan.json`
- `state/run_id_<ID>/discovery/execution_plan.md`

## Step 4 — Present evaluation report + execution plan and checkpoint

Present BOTH the Input Evaluation Report and the Execution Plan to the user.

The user reviews quality ("are my inputs good enough?") and scope ("here's what you'll build") together before committing. Checkpoint logic:
- `error` → halt, recommend fixing blockers
- `warn` → ask user to accept assumptions or fix inputs
- `pass` → proceed

Respond naturally based on the verdict. Let the user respond naturally.

If user re-runs after fixing: re-evaluate (max 3 iterations).

## Step 5 — Initialize run state and sync

Write all artifacts. Sync to outputs. Update session.json. Write phase_handoff.json.

Tell user: "Run `/compact focus on: run_id, phase status, user decisions, next steps` then run `/analyze-inputs`."

## Jira traceability

Follow the canonical traceability protocol in `.claude/skills/build-agent/references/jira_integration.md#traceability-protocol`. Phase summary line for this skill:

> `Build run started. Scope: <scope_list>. <N> tables in scope. Input evaluation: <one-line verdict>.`

## Required writes
- `state/run_id_<ID>/session.json`
- `state/run_id_<ID>/discovery/semantic_checks.json`
- `state/run_id_<ID>/discovery/input_evaluation_report.json`
- `state/run_id_<ID>/discovery/input_evaluation_report.md`
- `state/run_id_<ID>/discovery/execution_plan.json`
- `state/run_id_<ID>/discovery/execution_plan.md`
- `state/run_id_<ID>/phase_handoff.json`
- `memory/MEMORY.md`, `memory/DECISIONS.md` (phase boundary writes)
- Synced copies in `outputs/`
