# Checkpoint Format

Read this before any of the heavy phases prints to chat: `/start-build-run`, `/analyze-inputs`, `/plan-build`, `/generate-ddl`, `/generate-dml`, `/generate-dq`, `/generate-pipeline`, `/generate-tests`, `/evaluate-build`, `/revise-build`.

This file is the **single source of truth** for two things:

1. The **pre-flight preview** the supervisor prints at the *start* of every heavy phase.
2. The **next-phase preview** the supervisor appends to the end-of-phase HITL checkpoint.

Lightweight commands (`/status`, `/inspect-build`) are out of scope — they keep their current minimal output.

## Why

Before this file existed, users invoked phase commands blind: no idea what the agent was about to do, how long it might run, or what cost to expect. The end-of-phase checkpoint described what *just happened* but said nothing about what the next command would actually do. Both gaps are closed here.

## What goes on chat

### At phase start — pre-flight preview

```markdown
### About to run: `/<command>`

**What this does:** <one-line purpose from the command library below>

**Steps I'll execute:**
1. <plain-English step>
2. <step>
3. <step>
…

**ETA:** ~<low–high> min (run complexity = <low|moderate|high>)

**Cost:** I can't see token cost from inside the session. Run `/cost` in Claude Code (or check Cursor billing) before/after this command if you want to track spend.

Starting now…
```

Print this **before any tool call** in the phase. It is the first user-visible output.

### At phase end — next-phase preview

Print this **after** the existing HITL checkpoint (see `hitl_protocol.md`), as the final items.

```markdown
### What's next: `/<next-command>`

**What it will do:** <one-line purpose>

**Steps:**
1. <step>
2. <step>
…

**ETA:** ~<low–high> min (run complexity = <low|moderate|high>)

**Cost:** Run `/cost` before invoking to track spend for this phase.

When ready: run `/compact focus on: run_id, phase status, user decisions, next steps` (Claude Code) or start a new Agent session (Cursor), then `/<next-command>`.
```

When the next phase is conditional (e.g., evaluate-build can route to revise-build, or stop if no remediation items remain), print one preview block per realistic next command. When the run is terminal (evaluation passed cleanly or final revise-build cycle resolved all blockers), replace the preview with: `### Run complete — no further commands required.`

## ETA tiers

ETA is **tier-based**. The supervisor reads `complexity` from `session.json` (computed during `/start-build-run` per `input_validation.md`) and picks the matching column.

| Phase | Low | Moderate | High |
|---|---|---|---|
| `/start-build-run` | 2–4 min | 4–8 min | 8–15 min |
| `/analyze-inputs` | 3–6 min | 6–15 min | 15–30 min |
| `/plan-build` | 2–4 min | 4–8 min | 8–15 min |
| `/generate-ddl` | 1–3 min | 3–8 min | 8–15 min |
| `/generate-dml` | 3–10 min | 10–25 min | 25–60 min |
| `/generate-dq` | 1–4 min | 4–10 min | 10–20 min |
| `/generate-pipeline` | 1–3 min | 2–6 min | 4–10 min |
| `/generate-tests` | 2–6 min | 6–15 min | 15–30 min |
| `/evaluate-build` | 3–6 min | 6–12 min | 12–20 min |
| `/revise-build` | 2–5 min (targeted) | 5–12 min | 12–25 min (broad) |

If `session.json` does not exist yet (first-time `/start-build-run`), default to the `moderate` column for the pre-flight and revise once `complexity` is computed.

If `session.json.complexity` is missing on a legacy run, default to `moderate` and note it in the pre-flight: "*ETA assumes moderate complexity — actual `complexity` field not yet present in session.json.*"

## Cost reminder string (shared)

Use the exact wording above:

> I can't see token cost from inside the session. Run `/cost` in Claude Code (or check Cursor billing) before/after this command if you want to track spend.

Do **not** invent token-count estimates.

## Command library

Each entry below feeds both (a) the pre-flight when this command is being run, and (b) the next-phase preview when the previous phase ends recommending it.

### `/start-build-run`

- **What this does:** Inventory and classify all inputs, run structural and semantic checks, produce the Input Evaluation Report (pass/warn/error).
- **Steps:**
  1. Decide new run vs. continue; read memory and existing runs.
  2. Inventory and classify every file in `inputs/` recursively.
  3. Run structural checks (blockers, critical, major, minor findings).
  4. Run semantic anomaly checks and write `semantic_checks.json`.
  5. Generate the Input Evaluation Report (producible outputs matrix, findings, recommendations).
  6. Present the report and gate on verdict.
- **Next on pass/warn:** `/analyze-inputs`. **On error:** halt.

### `/analyze-inputs`

- **What this does:** Normalize all inputs, resolve conventions, and build the canonical model, source column registry, and derivation catalog.
- **Steps:**
  1. Read and validate all input files.
  2. Detect template conformance.
  3. Resolve convention priority chain (user instructions → memory → project → domain → enterprise → pattern → default).
  4. Delegate to `input-analyzer` sub-agent when STTM > 500 rows.
  5. Build `canonical_build_model.json`, `source_column_registry.json`, `derivation_catalog.json`.
  6. Extract and normalize DQ rules and relationships.
- **Next:** `/plan-build`.

### `/plan-build`

- **What this does:** Derive table dependencies, order tables into waves, and produce a per-table generation plan for every table in the run.
- **Steps:**
  1. Read the canonical model and source column registry.
  2. Derive dependencies from FK relationships and source lineage.
  3. Topologically sort tables into waves (dimensions before facts, lookups first).
  4. Produce per-table plans: DDL outline, DML strategy, DQ checks, test cases, confidence level.
  5. Mark low-confidence tables with notices.
  6. Write wave dependency graph and per-table plans.
- **Next:** `/generate-ddl`.

### `/generate-ddl`

- **What this does:** Generate CREATE TABLE statements for all planned tables. Skipped if DDL was not selected.
- **Steps:**
  1. Confirm `scope_selection.ddl = true`; read canonical model and conventions.
  2. Pre-size DDL per table and assign write strategies.
  3. For each wave, generate DDL wave-by-wave (delegate when > 5 tables).
  4. Validate every DDL from disk.
- **Next:** `/generate-dml` (or next selected type).

### `/generate-dml`

- **What this does:** Generate transformation and load scripts for all planned tables. Skipped if DML was not selected. This is the heaviest individual generate phase.
- **Steps:**
  1. Confirm `scope_selection.dml = true`; read conventions, source column registry, derivation catalog.
  2. Pre-validate all source column references against source_column_registry.json.
  3. Pre-size DML per table and assign write strategies (part-file for large tables).
  4. For each wave, generate DML wave-by-wave (delegate when > 5 tables).
  5. Validate every DML from disk (full checklist per quality_standards.md).
- **Next:** `/generate-dq` (or next selected type).

### `/generate-dq`

- **What this does:** Generate DQ check scripts for all planned tables. Output format driven by `dq_framework` convention. Skipped if DQ was not selected.
- **Steps:**
  1. Confirm `scope_selection.dq = true`; read `dq_framework` from conventions.
  2. For `custom` framework: confirm emission format with user.
  3. For each wave, generate DQ artifacts (delegate when > 5 tables).
  4. Validate: no nested aggregates, all column refs resolve to DDL.
- **Next:** `/generate-tests` (or `/evaluate-build` if tests not selected).

### `/generate-pipeline`

- **What this does:** Ask deployment platform (Databricks / Snowflake / Generic), read `lineage.json`, generate platform-specific pipeline orchestration YAML/SQL with dependency wiring, ingest tasks for L0 tables, and a deployment README.
- **Steps:**
  1. Ask user: Databricks Workflows / Snowflake Tasks / Generic YAML — lock `pipeline_platform` in session.json.
  2. Read `references/pipeline_conventions/{platform}.md` for output format rules.
  3. Validate `lineage.json` exists; warn if `lineage_reconciled = false`.
  4. Delegate to artifact-writer (pipeline mode) — generates one file per wave + master file.
  5. Validate pipeline files on disk; verify task count matches lineage table count.
- **Next:** `/generate-tests` (if tests selected) or `/evaluate-build`.

### `/generate-tests`

- **What this does:** Generate two categories of tests — (1) **data tests**: SQL/dbt assertions per table covering existence, uniqueness, not-null, SCD2 invariants, FK integrity, business-rule assertions; (2) **pipeline tests**: orchestration assertions covering task completeness, dependency wiring, wave isolation, idempotency, and platform-specific checks. Pipeline tests require pipeline artifacts to exist; skipped automatically if `/generate-pipeline` was not run.
- **Steps:**
  1. Confirm `scope_selection.tests = true`; determine which categories apply.
  2. Generate data tests wave by wave (delegate when > 5 tables); output to `tests_data/`.
  3. Generate pipeline tests if `generated/pipeline/` exists; output to `tests_pipeline/`.
  4. Validate both categories: not stubs, specific assertions, correct format per platform.
- **Next:** `/evaluate-build`.

### `/evaluate-build`

- **What this does:** Score every generated artifact against the evaluation rubric, apply the quality gate, and emit remediation items. Always runs in the `build-evaluator` sub-agent for context isolation.
- **Steps:**
  1. Inventory artifacts on disk (filesystem trumps state).
  2. Execute the faithfulness checklist.
  3. Score each dimension 0–10 with evidence from specific files.
  4. Apply gate rules → `passed` / `passed_with_actions` / `failed`.
  5. Write per-artifact scores and remediation items.
- **Next on `passed`:** Run complete — no further commands required. **On `passed_with_actions` or `failed`:** `/revise-build` first.

### `/revise-build`

- **What this does:** Apply targeted or broad fixes to generated artifacts while preserving stable IDs. Maximum 2 revision cycles per run.
- **Steps:**
  1. Classify feedback as targeted (≤ 3 tables) vs. broad.
  2. Edit only the affected artifacts; never reassign existing IDs.
  3. Validate revised artifacts from disk.
  4. Update session.json with revision metadata.
- **Next:** `/evaluate-build` (to re-score) or run complete (if remediation items are acceptable to waive). Run `/inspect-build` for a status summary.

## Worked example

Pre-flight at the start of `/evaluate-build` on a moderate-complexity run:

```markdown
### About to run: `/evaluate-build`

**What this does:** Score every generated artifact against the evaluation rubric, apply the quality gate, and emit remediation items.

**Steps I'll execute:**
1. Inventory artifacts on disk (filesystem trumps state).
2. Execute the faithfulness checklist.
3. Score each dimension 0–10 with evidence from specific files.
4. Apply the gate → passed / passed_with_actions / failed.
5. Write per-artifact scores and remediation items.

**ETA:** ~6–12 min (run complexity = moderate)

**Cost:** I can't see token cost from inside the session. Run `/cost` in Claude Code (or check Cursor billing) before/after this command if you want to track spend.

Starting now…
```

Next-phase preview at the end of the same `/evaluate-build` (gate = `passed_with_actions`):

```markdown
### What's next: `/revise-build` (recommended)

**What it will do:** Apply targeted or broad fixes to generated artifacts while preserving stable IDs.

**Steps (revise-build):**
1. Classify feedback as targeted vs. broad.
2. Edit only the affected artifacts; preserve IDs.
3. Validate revised artifacts from disk.
4. Update session.json with revision metadata.

**ETA:** ~5–12 min (run complexity = moderate, scope likely targeted)

**Cost:** Run `/cost` before invoking to track spend for this phase.

When ready: run `/compact focus on: run_id, phase status, user decisions, next steps` (Claude Code) or start a new Agent session (Cursor), then `/revise-build`. If remediation items are acceptable to waive, the run is complete — run `/inspect-build` for a status summary.
```
