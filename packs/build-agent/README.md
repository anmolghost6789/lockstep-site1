# Build Agent — STTM-to-Code Skill Package

**Version 5.4.0** | Author: ZS Associates

Build Agent is an AI skill package that turns source-to-target mappings and project context into production-ready ETL / ELT build artifacts. It runs inside **Cursor** or **Claude Code** — you talk to it in plain English, drop your files into a folder, and it does the rest.

It is designed for mixed teams: data engineers, analysts, architects, and project leads who may all contribute part of the input set. You do not need a perfect STTM bundle to get started. The agent inventories what exists, explains what is missing, and moves forward with clear confidence scores and evidence-backed outputs.

---

## Table of Contents

- [What This Package Does](#what-this-package-does)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the Agent — Step by Step](#running-the-agent--step-by-step)
- [Workflow Commands](#workflow-commands)
- [Workflow Diagram](#workflow-diagram)
- [Input Templates](#input-templates)
- [Runtime Folders](#runtime-folders)
- [Memory System](#memory-system)
- [Delegation for Large Runs](#delegation-for-large-runs)
- [Prompt Cookbook](#prompt-cookbook)
- [Troubleshooting / FAQ](#troubleshooting--faq)
- [Tool Compatibility](#tool-compatibility)
- [License](#license)

---

## What This Package Does

You put your project files into `inputs/`, tell the agent to start a build run, and it:

1. **Inventories and classifies** your inputs (mappings, data models, DQ rules, context docs, legacy SQL)
2. **Runs a quality gate** and tells you what is strong, what is weak, and what is missing
3. **Builds a canonical model** from the evidence it found
4. **Plans dependencies** and assigns generation waves
5. **Generates** DDL, DML, DQ checks, pipeline YAML, and tests — one `/generate-<artifact>` command at a time so you can inspect outputs between steps
6. **Evaluates quality** with deterministic scoring and a pass/fail verdict
7. **Revises issues** with controlled remediation (max 2 cycles)

At every major step the agent asks for your approval before proceeding. You stay in control.

---

## Prerequisites

- **Cursor** (any plan that supports agent mode) **or Claude Code** (CLI or IDE)
- Your project input files — at minimum, one spreadsheet or document that defines target tables and column mappings

No additional installs, dependencies, or API keys are needed beyond what your IDE already provides.

---

## Setup

### Option A — Use as a standalone project

Clone or download this repo and work directly inside it:

```bash
# Use the monorepo skill-packages/build-skill-package/ directory, or clone your org's repo.
cd skill-packages/build-skill-package
```

Then drop your files into `inputs/` and start a run (see below).

### Option B — Copy into an existing project

```bash
# Copy everything into your project root
cp -r Build-Agent-Skill-Package/* your-project/
```

Or selectively:

```bash
# Skills (Claude Code picks up the .claude/ directory automatically)
cp -r Build-Agent-Skill-Package/.claude/  your-project/.claude/

# Entry points
cp Build-Agent-Skill-Package/CLAUDE.md your-project/
cp Build-Agent-Skill-Package/AGENTS.md your-project/

# Context, inputs, and runtime folders
cp -r Build-Agent-Skill-Package/context/ your-project/context/
mkdir -p your-project/inputs your-project/runs your-project/outputs
cp -r Build-Agent-Skill-Package/runs/_memory/ your-project/runs/_memory/
```

---

## Running the Agent — Step by Step

### 1. Add your inputs

Place your project files into the `inputs/` folder. The agent classifies files by content, not by filename, so use whatever names make sense to you.

**Minimum to get started:** one file that defines target tables and columns (an STTM spreadsheet, a mapping doc, even a well-structured CSV).

**Recommended:** an STTM + a data model + at least one context document (enterprise, domain, or project).

**Ideal:** use the golden templates in `.claude/skills/build-agent/assets/templates/`, fill out what applies, and copy the completed files into `inputs/`.

### 2. Open the project in your IDE

Open the project folder in **Claude Code**. The agent skill is discovered automatically from the `.claude/` directory.

### 3. Start a build run

Type this in chat:

```
Start a new build run. Use all files in inputs/ and tell me what you found before planning anything.
```

The agent will:
- Read every file in `inputs/`
- Classify each file by content type
- Run the input quality gate
- Report what it found: what is strong, what is weak, what is missing
- Ask for your approval before moving to analysis

### 4. Follow the guided workflow

After the quality gate, the agent walks you through each phase in order:

| Phase | What happens | You decide |
|-------|-------------|------------|
| **Analyze** | Normalizes inputs, resolves naming conventions, builds a canonical model | Review the canonical model |
| **Plan** | Derives table dependencies, assigns generation waves, writes per-table plans | Review plans and wave order |
| **Generate** | Produces DDL, DML, DQ checks, pipeline YAML, and tests — one `/generate-<artifact>` command at a time, wave by wave inside each | Inspect outputs between artifact families |
| **Evaluate** | Scores every artifact deterministically, issues a verdict | Review the scorecard |
| **Revise** | Applies controlled fixes for any issues found (up to 2 cycles) | Approve revision scope |

You can also **inspect** at any time to see where things stand, or **continue** a previously interrupted run.

### 5. Pick up your outputs

Generated artifacts land in `outputs/` once each phase completes. The current workflow completes after evaluation and optional revision; download or package the synced `outputs/` tree from the playground when you need a handoff bundle.

---

## Workflow Commands

You can invoke any phase directly by name. The agent also accepts plain-English instructions — these are just the canonical command names.

| Command | What it does |
|---------|-------------|
| `/start-build-run` | Inventory inputs, run quality gate, initialize or resume run state |
| `/analyze-inputs` | Normalize inputs, resolve conventions, build the evidence-backed canonical model |
| `/plan-build` | Derive dependencies, assign waves, create per-table plans with confidence scores |
| `/generate-ddl` | Generate CREATE TABLE statements |
| `/generate-dml` | Generate transformation/load scripts (includes lineage reconciliation) |
| `/generate-dq` | Generate data quality check scripts |
| `/generate-pipeline` | Generate pipeline orchestration YAML (asks platform: Databricks/Snowflake/Generic) |
| `/generate-tests` | Generate data tests + pipeline tests |
| `/evaluate-build` | Score outputs deterministically, issue a pass/fail verdict, write remediation items |
| `/revise-build` | Apply controlled fixes after evaluation (max 2 cycles before escalation) |
| `/inspect-build` | Reconstruct run status from the filesystem, recommend next action |

---

## Workflow Diagram

```
/start-build-run   →  inventory inputs, quality gate, initialize state
        ↓
/analyze-inputs    →  normalize, resolve conventions, build canonical model
        ↓
/plan-build        →  dependency waves, per-table plans, output preferences
        ↓
/generate-ddl      →  CREATE TABLE statements
        ↓
/generate-dml      →  transformation/load scripts (includes lineage reconciliation)
        ↓
/generate-dq       →  data quality check scripts
        ↓
/generate-pipeline →  orchestration YAML (Databricks / Snowflake / Generic)
        ↓
/generate-tests    →  data tests + pipeline tests
        ↓
/evaluate-build    →  deterministic scoring, verdict, remediation actions
        ↓
/revise-build      →  controlled fixes, re-evaluate (max 2 cycles)

/inspect-build     →  status recovery from filesystem (use anytime)
```

Each `/generate-<artifact>` command runs separately so you can inspect outputs between steps. There is no orchestrator command; recommend the next step at phase end and let the user invoke it.

---

## Input Templates

The folder `.claude/skills/build-agent/assets/templates/` contains golden templates that define the optimal input structure. The agent is tuned to parse these formats with highest confidence, but they are never required — the agent works with any usable format.

Context documents (enterprise / domain / project) live at the package level under `context/guidance/` and are durable across runs. The same `.md` files appear in `assets/templates/` as starting points when you scaffold a new project.

### Excel templates

| File | Purpose |
|------|---------|
| `STTM_TEMPLATE.xlsx` | Source-to-target column mappings, transformation logic, and loading strategies |
| `DATA_MODEL_TEMPLATE.xlsx` | Target schema definition, column metadata, and table relationships |
| `DQ_RULES_TEMPLATE.xlsx` | Data quality checks with severity, thresholds, and SQL expressions |

### Context documents (Markdown)

| File | Purpose |
|------|---------|
| `enterprise_context.md` | Organization-wide platform, standards, and naming conventions |
| `domain_context.md` | Business domain, source systems, entity definitions |
| `project_context.md` | Project scope, timeline, and output expectations |
| `user_instructions.md` | Hard constraints and must-follow rules for this run |
| `business_rules.md` | Complex transformation logic and SCD behavior |
| `known_gaps.md` | Documented uncertainties and missing inputs |
| `legacy_patterns.sql` | Reference implementation SQL from existing systems |

### How the agent resolves conflicts

When conventions conflict across documents, the agent uses this priority chain (highest to lowest):

1. User instructions
2. Active memory from prior runs
3. Project context
4. Domain context
5. Enterprise context
6. Dominant input pattern
7. Sensible default

See `.claude/skills/build-agent/assets/templates/HOW_TO_USE_TEMPLATES.md` for a detailed guide on every template file.

---

## Runtime Folders

These five folders are the agent's working surface. Do not rename them.

| Folder | Purpose | Who writes to it |
|--------|---------|-----------------|
| `inputs/` | Active per-run project files — mappings, models, DQ rules, business rules, legacy SQL | You |
| `context/` | Durable cross-run guidance — `branding/`, `guidance/` (enterprise/domain/project), `reference/` | You (rarely) |
| `runs/` | Each run lives at `runs/run_id_<ID>/` with its own `state/`, `outputs/`, snapshots, logs | Agent |
| `runs/_memory/` | Durable facts, conventions, and decisions that persist across runs (CONVENTIONS.md, DECISIONS.md, MEMORY.md, PATTERN_LIBRARY.md) | Agent (with your approval) |
| `outputs/` | Mirror of the active run's `outputs/`, for download / handoff | Agent |

**How data flows:** During active phase work, the agent writes inside `runs/run_id_<ID>/`. Completed artifacts are synced from the run dir's working area to its `outputs/` at the end of each phase. The top-level `outputs/` folder is a convenience mirror — the run dir is authoritative.

---

## Memory System

The `runs/_memory/` folder gives the agent durable knowledge that persists across runs. It contains four files:

| File | What it stores |
|------|---------------|
| `CONVENTIONS.md` | Naming rules, coding style, platform standards, audit patterns |
| `DECISIONS.md` | Rationale-backed decisions made during prior runs |
| `MEMORY.md` | General observations — source system quirks, client preferences, data notes |
| `PATTERN_LIBRARY.md` | Reusable SQL patterns learned from generation and evaluation |

Each entry is tagged with a status (`active`, `superseded`, `retired`), a source, and a run ID. The agent reads memory at the start of every run and writes back discoveries at the end. Later entries can supersede earlier ones without deleting history.

Memory starts empty. Seed templates showing the expected format are in `.claude/skills/build-agent/assets/templates/memory/`.

Per-subagent project memory lives separately at `.claude/agent-memory/<subagent>/` and is curated by the `learnings-curator` subagent at run end.

---

## Delegation for Large Runs

For runs with more than 10 tables or large input sets, the agent can delegate phase work to sub-agents. This keeps each phase focused and prevents context overflow.

- **Claude Code**: uses the native Task tool for process-isolated sub-agents
- **Cursor**: uses instructional delegation (the agent scopes each phase as a contained task)

In both cases the filesystem is the shared state. Each phase reads from disk, writes to disk, and produces a compressed handoff summary. You do not need to configure anything — the agent decides when delegation is appropriate.

---

## Prompt Cookbook

### Start a new run

```
Start a new build run. Use all files in inputs/ and give me the input quality findings before moving to analysis.
```

### Continue an existing run

```
Continue the existing build run. Read runs/_memory/ and the latest runs/run_id_*/ first, tell me where the run stands, and recommend the next step.
```

### Inspect current status

```
Inspect the current build run from disk and tell me what is complete, what is missing, and what I should do next.
```

### Force the agent to use all available inputs

```
Use every relevant file in inputs/. Do not ignore notes or reference files just because they are not named like an STTM.
```

### Prioritize specific files

```
Use all inputs, but prioritize user_instructions.md and business_rules.md when conventions conflict.
```

### Proceed with missing inputs

```
If inputs are incomplete, explain the impact clearly and then proceed with documented assumptions where possible.
```

### Review low-confidence tables before generation

```
Before generating code, show me the lowest-confidence tables, the gaps behind them, and any assumptions you would make.
```

### Run evaluation

```
Evaluate the current generated outputs from disk, show me the verdict, and list the remediation items in priority order.
```

### Revise issues

```
Revise the build using the current remediation items. Start with blockers and must-fix issues, then re-evaluate the affected scope.
```

---

## Troubleshooting / FAQ

**"I only have one spreadsheet."**
That works if it has usable mapping content. The Input Evaluation Report will flag what is missing. The agent will proceed with assumptions documented inline.

**"My notes or context files are not being used."**
Make sure they are in `inputs/`. Then tell the agent explicitly which files should take priority.

**"How do I know what the agent assumed?"**
Add an `enterprise_context.md`, `project_context.md`, or `user_instructions.md` so the agent can resolve conventions without asking.

**"The run feels low-confidence."**
Ask the agent to list the lowest-confidence tables before generation and explain which missing inputs would improve scores.

**"I want a specific output structure or naming style."**
Say so early — ideally in `user_instructions.md` and again in chat before planning is approved.

**"My run was interrupted. Can I pick up where I left off?"**
Yes. The agent persists progress to `runs/run_id_<ID>/session.json`. Say "Continue the existing build run" and it will recover from the last completed phase.

**"I want to skip a phase."**
You can invoke any command directly (e.g., `/generate-ddl`) and the agent will check whether prerequisites are met. If they are not, it will tell you what to do first.

**"How do I start over?"**
Delete (or move) the `runs/run_id_<ID>/` folder you want to discard, then start a new run. Durable memory in `runs/_memory/` is preserved so the agent remembers conventions from prior runs.

**"The agent overrode my instruction."**
The agent records waivers and discloses deviations at checkpoints. If the agent disagrees with an instruction (e.g., you specified INNER JOIN but the agent recommends LEFT JOIN), it will record a waiver explaining its concern and document it as a waiver at the phase boundary. Check the assumptions register for all documented deviations. Silent overrides are no longer permitted.

**"DQ/tests were generated for more tables than I specified."**
Check the Input Evaluation Report for assumptions and the generated artifacts for inline [ASSUMPTION] notices.

**"The `/commands` don't autocomplete in my IDE."**
Each workflow command is a top-level skill at `.claude/skills/<command-name>/SKILL.md`. Make sure the directory exists in your project root with one folder per command (`start-build-run/`, `analyze-inputs/`, `generate-ddl/`, …). The package no longer ships a separate `.claude/commands/` folder — skills are the single source of truth.

**"I want DQ emitted as dbt tests, not procedural SQL."**
Set `DQ framework: dbt_tests` in your `enterprise_context.md` (or override in `project_context.md` / `user_instructions.md`). Supported values: `sql_procedural` (default), `dbt_tests`, `great_expectations`, `deequ`, `custom`. The agent branches emission format during `/generate-dq`.

**"My target isn't Snowflake — will generated SQL be correct?"**
Set the target dialect in `context/guidance/enterprise_context.*::SQL Dialect` (supported: `snowflake`, `bigquery`, `synapse`, `databricks`, `redshift`). The agent emits dialect-specific SQL and, during `/evaluate-build`, runs a dialect-compatibility scan that flags cross-dialect functions. See `.claude/skills/build-agent/assets/templates/legacy_patterns.sql` for dialect-tagged reference patterns you can tailor per project.

---

## Tool Compatibility

| Tool | Skills directory | Entry point | Notes |
|------|-----------------|-------------|-------|
| Claude Code | `.claude/skills/` | `CLAUDE.md` | Primary target — Claude models only |
| OpenCode / Codex | `.claude/skills/` or `.agents/skills/` | `AGENTS.md` | Model-agnostic; reads the same skill files |

Every workflow command is a sibling skill under `.claude/skills/`; the `build-agent/` skill is the orchestrator that delegates to the per-phase skills. There is no separate commands directory.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
