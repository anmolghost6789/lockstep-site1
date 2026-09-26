# Command reference

Every user-facing action in this package is one of these seven slash commands, plus one
hidden shared-protocol skill that the phase skills load automatically. All seven commands
live under `.claude/skills/<command-name>/SKILL.md`.

## Phase commands

| Command | When to run it | What it reads | What it writes |
|---|---|---|---|
| `/start-design-run` | First command for a new or materially changed design. | `inputs/` (all categories), `context/guidance/`, prior `outputs/00_state/run_state.json` if resuming. | Input snapshot, UTF-8 ingest sidecars, `input_index.json`, `input_set_evaluation_report.md` (published to `outputs/01_inputs/`), `source_decisions.json` + `source_gap_report.md` (published to `outputs/02_sources/`). |
| `/design-architecture` | Inputs and source choices are ready for design. | `input_index.json` + sidecars, `source_decisions.json` (`status: "selected"` entries and waivers only), `context/guidance/`, governed reference patterns. | `column_mappings.json`, `dq_rules_design.json`, `target_model_design.md` (rendered), `design_brief.md`, `plan.json` — published to `outputs/03_design/` and `outputs/04_plan/`. |
| `/generate-artifacts` | The stated design is ready for rendering. | `column_mappings.json`, `dq_rules_design.json`, `plan.json`, canonical workbook templates. | Per-layer `STTM_{layer}.xlsx`, `DATA_MODEL_{layer}.xlsx`, `DQ_{layer}.xlsx`, `ER_DIAGRAM_{layer}.md`; whole-flow `ER_DIAGRAM.xlsx` and `ER_DIAGRAM_LINEAGE.md` — all under `outputs/05_artifacts/`. |
| `/evaluate-design` | Generated artifacts are ready for a quality gate. | Every generated artifact, `column_mappings.json`, `dq_rules_design.json`, `header_check.json`, `semantic_check.json`. | `evaluation_report.md`, `evaluation_scores.json` (published to `outputs/06_evaluation/`); on approval, also updates `memory/`, resolves the reference-store decision, cleans `outputs/00_state/runtime_scratch/`, and marks the run completed. |

## Utility commands

| Command | When to run it | What it does |
|---|---|---|
| `/refresh-reference-store` | Governed raw reference material under `context/reference/raw/` changed. | Rebuilds processed reference-store patterns (`context/reference/processed/`) from raw material. User-invoked only; mutates persistent governed knowledge. |
| `/status` | You need a brief orientation without changing any work. | Reads `outputs/00_state/run_state.json` and reports run ID, status, current stage, `awaiting_user_action`, stage history, and links to generated artifacts. Never advances a stage. |
| `/cancel` | You need to stop an active run. | Asks for confirmation, then preserves `outputs/` (deliverables and agent state) while clearing user-provided files from `inputs/` (README.md files are kept). |

## Hidden shared protocol

`design-agent` (`.claude/skills/design-agent/SKILL.md`) is `user-invocable: false`. It is
the shared protocol the four phase skills load for common rules: phase-boundary
discipline, source-selection integrity, context precedence, subagent thresholds, and the
`design facts before files` principle. You never invoke it directly.

## Subagents (not slash commands)

These are `.claude/agents/*.md` definitions the phase skills spawn under specific
thresholds — they are not user-invocable commands:

| Subagent | Spawned by | Threshold |
|---|---|---|
| `input-analyzer` | `/start-design-run` | More than 15 input files, or snapshot size over 15 MB, or more than 30 declared source tables. Fans out two instances in parallel (`scope=requirements`, `scope=sources`). |
| `design-writer` | `/design-architecture` | Escape hatch only — a single layer with more than 10 tables, the first 3 tables of that layer averaging over 90s each, and orchestrator context estimated over 120k tokens. |
| `artifact-writer` | `/generate-artifacts` | Rarely needed — more than 15 target tables and generation demonstrably needs per-layer supervision. Still only invokes the shipped `generate_workbooks.py`. |
| `design-evaluator` | `/evaluate-design` | Always spawned for this phase. |

## Next

See [Phases](../workflow/phases.md) for the end-to-end workflow shape, or
[Configuration](../reference/configuration.md) for the scripts and templates these
commands invoke.
