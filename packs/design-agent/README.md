# Design Agent

Design Agent converts approved business requirements and source information into the
design artifacts an engineering team needs before implementation: source-to-target
mappings (STTM), layered data-model workbooks, data-quality rules, and ER diagrams. It
records the design facts first — canonical mappings and DQ rules in two JSON files — then
generates every visible workbook, diagram, and review document from those facts with
deterministic scripts.

## Scope and lifecycle position

Design is the second stage of the data-engineering delivery lifecycle:

```text
Requirements -> Design -> Build -> Deploy -> Test
```

Use Design after Requirements has established the business scope, behavior, and key data
needs. Use Build after Design has produced, and a human has reviewed, the mappings and
target model — Build turns them into DDL/DML, DQ checks, and pipeline orchestration; Design
never writes that implementation code itself.

| Design owns | Design does not own |
|---|---|
| Source selection, target structure, mappings, lineage, DQ rules, and artifact generation. | Inventing missing source facts, writing production DDL/DML, deploying pipelines, or executing production tests. |
| Transparent gap and waiver handling. | Treating a template as evidence or silently replacing a source decision. |
| STTM, data model, DQ, and ER deliverables. | Making business-scope decisions that belong in Requirements. |

## Prerequisites

- A current Claude Code installation and an authenticated Claude account.
- Git, if you will clone or contribute changes.
- Python 3.10+, for the package's deterministic scripts:
  - `openpyxl>=3.1.2,<4.0.0` — template-based workbook generation and header verification.
  - `sqlglot>=23.0.0` — DQ rule expression SQL parsing during evaluation.

Full detail, including local-settings setup: [Prerequisites](docs/getting-started/prerequisites.md).

## Install and open it in Claude Code

```powershell
Set-Location .\skill-packages\design-skill-package
Copy-Item .claude\settings.template.json .claude\settings.json
python -m pip install -r .claude\skills\design-agent\scripts\requirements.txt
claude
```

The local settings file controls command permissions and runtime limits. It contains no
client credential. Keep any organization-specific credentials outside versioned package
files. Open the package root so `CLAUDE.md`, phase skills, templates, and hooks are
discovered together — opening a parent folder or a subfolder such as `.claude/` can produce
an incomplete workflow.

## Prepare the inputs

| Folder | Put this here | Used for |
|---|---|---|
| `inputs/requirements/` | Approved BRDs/FRDs, scope, entities, acceptance criteria. | Business intent and required outcomes. |
| `inputs/source_inventory/` | Source systems, schemas, catalogs, metadata, samples. | Source selection and source-grain decisions. |
| `inputs/additional_documents/` | KPIs, business rules, DQ requirements, legacy designs, supporting material. | Additional evidence and constraints. |
| `inputs/instructions/` | Run-specific instructions and hard boundaries. | Scope and handling constraints. |
| `context/guidance/` | Enterprise, domain, and project rules. | Durable design conventions. |
| `context/branding/` | Workbook branding preferences. | Presentation, not design facts. |
| `context/reference/` | Governed patterns and prior examples (optional). | Approved reference material. |

Do not execute a user-provided script as input. Do not place a raw production data extract
or credential in the package. The package uses supplied sources to derive design evidence
and leaves a gap visible when an answer cannot be supported.

## Run the design workflow

```text
/start-design-run
  -> evaluate inputs, snapshot evidence, select sources, report gaps
/design-architecture
  -> state mappings, DQ rules, target architecture, lineage, and plan
/generate-artifacts
  -> generate workbook and ER outputs from the canonical design facts
/evaluate-design
  -> verify artifacts, capture governed learnings, close the run
```

Each command is a phase boundary. The agent writes state at phase start and completion,
recommends the next command, and stops. A user starts the next phase only after reviewing
the result — the workflow never auto-chains.

## Command reference

| Command | When to run it | What it produces |
|---|---|---|
| `/start-design-run` | First command for a new or materially changed design. | Input readiness, input snapshot, `source_decisions.json`, and source-gap report. |
| `/design-architecture` | Inputs and source choices are ready for design. | Canonical mappings, DQ rules, design brief, review markdown, lineage, and generation plan. |
| `/generate-artifacts` | The stated design is ready for rendering. | Per-layer STTM, data model, DQ workbooks, and ER outputs. |
| `/evaluate-design` | Generated artifacts are ready for a quality gate. | Deterministic and semantic evaluation, governed learnings, runtime cleanup, completed state. |
| `/refresh-reference-store` | Governed raw reference material changed. | Refreshed processed reference patterns. |
| `/status` | You need a brief orientation without changing work. | Current state and recommended next action. |
| `/cancel` | You need to stop an active run. | Preserves the existing output tree after confirmation. |

`design-agent` (`.claude/skills/design-agent/SKILL.md`) is a hidden, non-user-invocable
shared protocol the four phase skills load automatically. Full detail, including
subagent thresholds: [Command reference](docs/how-to-run/command-reference.md).

## Design facts before files

The core design is stored as canonical facts—especially column mappings and DQ rules—not
as several independently edited workbook views. The package uses deterministic renderers
and generators to create the review markdown, workbooks, and diagrams. If an output is
wrong, correct the stated design fact and regenerate; do not manually patch multiple
derived artifacts until they disagree.

This protects traceability and makes a rerun meaningful. It also explains why the
architecture phase is the principal review gate: the generator should render an approved
design, not create a different design during a spreadsheet export.

## Folder structure

```text
design-skill-package/
  CLAUDE.md                  package rules and phase-flow summary
  README.md                  this file
  workspace_layout.yaml       playground UI + run-scaffold contract
  .mcp.json                  declared MCP server endpoints (jira, github — unused by any skill today)
  config/
    project_config.json      naming, layering, DQ, and context-hierarchy defaults
  context/                   durable, cross-run guidance and reference (see below)
  inputs/                     run-specific evidence (see below)
  memory/                     durable operational learnings (5 markdown files)
  .claude/
    settings.template.json   versioned settings template
    skills/
      start-design-run/       design-architecture/       generate-artifacts/
      evaluate-design/         refresh-reference-store/    status/    cancel/
      design-agent/            hidden shared protocol skill
      data-artifact-generation/  (empty; not an active skill)
    agents/
      input-analyzer.md   design-writer.md   artifact-writer.md   design-evaluator.md
    hooks/                  reserved, no active hooks shipped
    rules/                  reserved, no always-on rule files shipped
  outputs/                   single working tree (00_state/ .. 06_evaluation/), gitignored
```

## Outputs and state

```text
outputs/
  00_state/                 private run state, snapshots, scratch, logs, evaluation
  01_inputs/                normalized input view
  02_sources/               source discovery and selection evidence
  03_design/                stated design facts and review material
  04_plan/                  execution plan and dependencies
  05_artifacts/{layer}/     STTM_{layer}.xlsx, DATA_MODEL_{layer}.xlsx, DQ_{layer}.xlsx
  06_evaluation/            user-readable quality results
```

The global ER diagram sits with the generated artifacts. `outputs/00_state/` is internal
control state and must not be handed to Build as a deliverable. Hand off the reviewed
STTM, data model, DQ rules, ER diagram, relevant design brief, and explicitly accepted
gaps/waivers. Full folder-by-folder detail: [Inputs and outputs](docs/workflow/inputs-and-outputs.md).

## Configuration

`config/project_config.json` is the package's central defaults file: naming and layer
prefix patterns, standard audit columns, surrogate-key strategy, default DQ check
thresholds, the context-hierarchy tiers, supported input formats, and subagent spawn
thresholds. Five YAML contracts under `.claude/skills/design-agent/specs/` (artifact,
template, validation, traceability, run-state) provide the same information as
machine-readable checklists. Four canonical `.xlsx` templates under
`.claude/skills/design-agent/templates/workbooks/` control workbook structure and default
formatting — the generator scripts hardcode no palette. Full detail:
[Configuration](docs/reference/configuration.md).

## Review checklist before Build

1. Confirm the selected sources and source grain are correct.
2. Review mappings for every target column, including derivation, joins, filters, and
   source references.
3. Confirm layer ordering and same-layer dependencies are either absent, sub-layered, or
   formally waived.
4. Confirm each DQ rule has a clear rule, scope, and source-backed reference.
5. Open the generated STTM and data model; do not review only the summary markdown.
6. Run `/evaluate-design` and resolve material findings before Build uses the artifacts.

## Safe recovery and troubleshooting

| Situation | Safe response |
|---|---|
| Input readiness is blocking. | Add the missing requirements or source evidence; do not start architecture on a guessed source set. |
| A source was rejected or a gap is reported. | Resolve it in the source decision or record a waiver before design. |
| Generated workbook looks wrong. | Check the canonical mapping/DQ fact and re-run the generator. |
| A run was interrupted. | Run `/status` and inspect `outputs/00_state/run_state.json`; do not delete outputs. |
| A design fact changes after review. | Re-enter the affected phase, regenerate affected artifacts, and re-evaluate. |

Every phase is idempotent on re-entry — resuming after an interruption continues from the
first missing or stale step rather than restarting. Full detail:
[Revisions and recovery](docs/workflow/revisions-and-recovery.md).

## Full documentation

| Category | Page | Covers |
|---|---|---|
| Getting started | [Overview](docs/getting-started/overview.md) | What Design Agent is, what it owns/does not own, lifecycle position, key concepts, main outputs. |
| Getting started | [Prerequisites](docs/getting-started/prerequisites.md) | Claude Code, Python, dependency installs, local settings. |
| Getting started | [Quick start](docs/getting-started/quick-start.md) | Fastest concrete path to a first run. |
| How to run | [Running in Claude Code](docs/how-to-run/running-in-claude-code.md) | Local install, daily operating loop, resuming, recovery. |
| How to run | [Running via the marketplace](docs/how-to-run/running-in-marketplace.md) | The hosted Guided UI, and how it relates to direct Claude Code use. |
| How to run | [Command reference](docs/how-to-run/command-reference.md) | Every command and subagent: when to use it, what it reads, what it writes. |
| Workflow | [Phases](docs/workflow/phases.md) | End-to-end phase-by-phase workflow, checkpoint model, review points. |
| Workflow | [Inputs and outputs](docs/workflow/inputs-and-outputs.md) | Folder-by-folder table for `inputs/`, `context/`, `outputs/`, `memory/`. |
| Workflow | [Revisions and recovery](docs/workflow/revisions-and-recovery.md) | Change-impact routing, `/status`, idempotent re-entry, `/cancel`. |
| Reference | [Configuration](docs/reference/configuration.md) | `workspace_layout.yaml`, `config/`, specs, knowledge base, scripts, templates. |
| Reference | [Troubleshooting FAQ](docs/reference/troubleshooting-faq.md) | Realistic answers to common blockers and errors. |
