---
name: build-agent
description: >-
  Turn source-to-target mappings, data models, DQ rules, legacy SQL, and project context into production-ready ETL/ELT build artifacts (DDL, DML, DQ checks, pipeline orchestration, tests). Works with messy or incomplete inputs and produces everything inputs support — no scope exclusion; thin-evidence tables get documented notices, not omission. Use when the user wants to build, generate, or produce ETL/ELT code, data pipelines, or warehouse build artifacts from mappings/models.
compatibility:
  - claude-code
  - cursor
metadata:
  author: ZS Associates
---

# Build Agent

Build Agent is a skill package for end-to-end STTM-to-code generation. It inventories inputs, generates an Input Evaluation Report, builds an evidence-backed canonical model, plans dependency-ordered generation, produces ALL artifacts, evaluates quality deterministically, remediates issues, and packages for delivery.

The agent produces **everything the inputs support**. There is no scope exclusion. Tables with thin evidence get `[ASSUMPTION]` or `[INSUFFICIENT INPUT]` inline notices, not omission.

The agent is **non-interactive during phases**. User interaction happens only at phase boundaries.

## Package boundary

### Package assets
- `.claude/skills/` — orchestrator at `build-agent/` + per-phase skills as siblings
- `.claude/agents/` — sub-agents
- `.claude/agent-memory/` — project-scoped subagent memory
- `.claude/hooks/` — SessionStart, PreToolUse, PostToolUse, Stop
- `.claude/skills/build-agent/assets/templates/` — golden input templates
- `.claude/skills/build-agent/scripts/` — shared Python tools (sync_outputs, validate_artifacts, patch_session, append_log)
- `CLAUDE.md` / `AGENTS.md` / `README.md`
- `.mcp.json` (github + jira MCP)

### Runtime artifacts
- `inputs/` — active per-run inputs (sttm, data_model, dq_rules, business_rules, legacy_code, known_gaps, additional_documents)
- `context/` — durable cross-run context (branding, guidance, reference)
- `runs/run_id_<ID>/` — active run workspace (state, plans, generated, evaluation, outputs, memory)
- `runs/_memory/` — durable cross-run package memory
- `outputs/` — mirror of the active run's `outputs/` for download/handoff

## Operating principles

### 1. No mid-phase questions
While a command is running, never ask the user anything. Make safe assumptions, document them, present at phase end only.

### 2. Produce everything you can
No scope exclusion. Generate artifacts for ALL planned tables. Thin-evidence tables get documented notices.

### 3. Filesystem is the source of truth
Validate and evaluate from disk. Never trust conversation context.

### 4. Mandatory sub-agent delegation
When > 5 tables, > 500 STTM rows, or during evaluation. Pre-configured sub-agents in `.claude/agents/`.

### 5. Context hygiene between phases
Compact or clear context between phases. Write `phase_handoff.json` for continuity.

### 6. Evidence must travel forward
Every artifact traces to canonical model, conventions, and derivation catalog.

### 7. State-first writes
Write inside the run dir at `runs/run_id_<ID>/` during phases, sync to its `outputs/` at phase end.

### 8. Instruction deviations must be disclosed
Record as waivers. Convention priority: user instructions > runs/_memory > project > domain > enterprise > pattern > default.

### 9. Low-confidence work cannot hide
Document uncertainty clearly and lower confidence.

### 10. The run ledger must stay current
Update session.json and phase_handoff.json after every significant step.

## Delegation

Pre-configured sub-agents in `.claude/agents/`:
- `input-analyzer` — normalization and canonical model (when > 500 STTM rows)
- `artifact-writer` — artifacts per wave (when > 5 tables)
- `build-evaluator` — evaluation (always)

## Required references

Read at the right time:
- `references/runtime_contract.md` — before any writes
- `references/input_validation.md` — during `/start-build-run`
- `references/checkpoint_format.md` — before printing the pre-flight preview at the start of any heavy phase
- `references/hitl_protocol.md` — at phase boundaries
- `references/quality_standards.md` — before any `/generate-*` command
- `references/evaluation_rubric.md` — before `/evaluate-build`
- `references/remediation_and_packaging.md` — before `/revise-build`
- `references/delegation_protocol.md` — before delegating

## Workflow

### `/start-build-run`
- Check Python dependencies (Step -1)
- Ask user which artifact types to generate — DDL / DML / DQ / Tests (Step 0, scope_selection locked in session.json)
- New or continue
- Read memory; inventory and classify inputs
- Run structural + semantic checks
- Generate Input Evaluation Report (pass/warn/error)

### `/analyze-inputs`
- Normalize inputs via sub-agent (when above threshold)
- Detect template conformance; resolve conventions (write conflicts_resolved[])
- Build canonical model, source column registry, derivation catalog

### `/plan-build`
- Derive dependencies and waves
- Per-table plans for ALL tables in selected scope
- Mark low-confidence with notices

### `/generate-pipeline`
- Ask deployment platform: Databricks Workflows / Snowflake Tasks / Generic YAML
- Read `plans/lineage.json` (written by /plan-build; reconciled by /generate-dml)
- Read `references/pipeline_conventions/{platform}.md`
- Delegate to artifact-writer (pipeline mode): generate task files, dependency wiring, deployment README
- Verify reconciliation status; note if using planned (unreconciled) lineage

### Generation — user-driven, one artifact family at a time

The user invokes each `/generate-<artifact>` command separately so they can
inspect outputs between steps. There is no orchestrator command and no
auto-chaining — recommend the next step at phase end, do not invoke it.

- `/generate-ddl` — CREATE TABLE statements only
- `/generate-dml` — transformation/load scripts only (includes lineage reconciliation as final step)
- `/generate-dq` — DQ check scripts only (format driven by dq_framework)
- `/generate-pipeline` — pipeline orchestration YAML only (asks platform; reads reconciled lineage.json)
- `/generate-tests` — data tests + pipeline tests (pipeline tests skipped if no pipeline artifacts exist)

Each generate command respects `scope_selection` from session.json. Unselected types are skipped cleanly. Recommended invocation order: DDL → DML → DQ → Pipeline → Tests.

### `/evaluate-build`
- Delegated to build-evaluator (always)
- Deterministic scoring, gate, remediation

### `/revise-build`
- Apply fixes, max 2 cycles

### `/inspect-build`
- Filesystem recovery

### `/status`
- Quick orientation after context reset

## Commands

| Command | Purpose |
|---------|---------|
| `/start-build-run` | Check Python deps, select scope (DDL/DML/DQ/Pipeline/Tests), evaluate inputs |
| `/analyze-inputs` | Build canonical model |
| `/plan-build` | Dependency waves, per-table plans, lineage.json |
| `/generate-ddl` | Generate DDL only |
| `/generate-dml` | Generate DML only (includes lineage reconciliation) |
| `/generate-dq` | Generate DQ checks only |
| `/generate-pipeline` | Generate pipeline orchestration YAML (asks platform: Databricks/Snowflake/Generic) |
| `/generate-tests` | Generate data tests + pipeline tests |
| `/evaluate-build` | Score and remediate (always delegated) |
| `/revise-build` | Apply fixes (max 2 cycles; patches lineage if tables changed) |
| `/inspect-build` | Recover from disk |
| `/status` | Quick status check |
