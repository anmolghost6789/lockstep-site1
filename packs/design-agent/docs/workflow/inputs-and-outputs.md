# Inputs and outputs

## `inputs/` — run-specific evidence

| Folder | Put this here | Used for |
|---|---|---|
| `inputs/requirements/` | Approved BRDs/FRDs, scope, entities, acceptance criteria. | Business intent and required outcomes. |
| `inputs/source_inventory/` | Source systems, schemas, catalogs, metadata, samples — may include the full source universe, not only sources you expect to use. | Source selection and source-grain decisions. |
| `inputs/additional_documents/` | KPIs, business rules, DQ requirements, legacy designs, supporting material. | Additional evidence and constraints. |
| `inputs/instructions/` | Run-specific directives and hard boundaries. Recommended filename stem: `user_instructions`. | Scope and handling constraints; parsed as the narrowest context tier. |

Each category folder ships a `README.md` describing its expected content in more detail.
`README.md` files (and `.gitkeep`/`.keep`/`.DS_Store`) are package guidance, never counted
as run evidence — if every category holds only these, `/start-design-run` will not start a
run. `inputs/midrun_uploads/` is created only at runtime, during an in-phase clarification,
and is otherwise absent from the scaffold.

Supported formats across `inputs/` and `context/`: DOCX, TXT, XLSX, XLS, ZIP, PPTX, PPT,
PDF, CSV, TSV, MD, PY, JSON, XML, YAML, YML. A user-provided `.py` file is parsed as text
only and is never executed.

Do not place a raw production data extract or a credential anywhere under `inputs/`.

## `context/` — durable, cross-run material

```text
context/
  branding/
  guidance/
    enterprise_context/
    domain_context/
    project_context/
  reference/            (optional — created only if you use it)
    raw/
    processed/
    _metadata.json
```

| Folder | Contains | Authority |
|---|---|---|
| `context/guidance/enterprise_context/` | Org-wide standards, governance, glossary, policies. | Broadest tier. |
| `context/guidance/domain_context/` | Business-domain standards inside the enterprise (a sub-area such as Commercial Sales or Manufacturing — not the enterprise's industry). | Second tier. |
| `context/guidance/project_context/` | Project-scope guidance, platform constraints, naming overrides. | Third tier. |
| `context/branding/` | Optional workbook branding/presentation preferences. Presentation only — never a design fact. | Not part of the guidance hierarchy. |
| `context/reference/` | Governed, reusable patterns from prior runs (approved via the `/evaluate-design` closure tail). Advisory only; current-run evidence always wins. | Consulted after all guidance tiers. |

Context precedence, highest first: confirmed clarifications > `inputs/instructions/` user
instructions > `project_context` > `domain_context` > `enterprise_context` > governed
reference-store patterns > built-in package defaults. A lower tier may override a higher
tier only with explicit human confirmation.

## `outputs/` — the single working tree

There is no per-run `runs/` folder and no publish/mirror step: each phase writes its
user-facing deliverable directly into its numbered folder, and keeps agent-internal state
under `outputs/00_state/`.

```text
outputs/
  00_state/                 private run state, snapshots, scratch, logs, evaluation
    run_state.json          internal control ledger
    input_snapshot/         snapshot of inputs/ at run start
    context_snapshot/       snapshot of context/guidance/ at run start
    source_discovery/       source_decisions.json, source_gap_report.md (working copy)
    design/                 column_mappings.json, dq_rules_design.json, target_model_design.md, design_brief.md
    execution_plan/         plan.json (working copy)
    evaluation/             header_check.json, semantic_check.json, evaluation_report.md, evaluation_scores.json (working copy)
    runtime_scratch/        temporary generated code only — cleaned at /evaluate-design close
    logs/                   runtime code manifest, input cleanup report
    handoffs/                artifact-writer fan-out coordination only
    traceability/           evidence_registry.json
  01_inputs/                published input_set_evaluation_report.md
  02_sources/               published source_decisions.json, source_gap_report.md
  03_design/                published design_brief.md, target_model_design.md, column_mappings.json, dq_rules_design.json
  04_plan/                  published plan.json (plus plan.md if written)
  05_artifacts/{layer}/     STTM_{layer}.xlsx, DATA_MODEL_{layer}.xlsx, DQ_{layer}.xlsx, ER_DIAGRAM_{layer}.md
  05_artifacts/             ER_DIAGRAM.xlsx, ER_DIAGRAM_LINEAGE.md (whole-flow, all layers)
  06_evaluation/            published evaluation_report.md, evaluation_scores.json
```

`outputs/00_state/` is internal control state and must never be handed to Build as a
deliverable, deleted to "start over", or hand-edited. Use `/status`, `/cancel`, or a
targeted revision instead (see [Revisions and recovery](revisions-and-recovery.md)). Hand
Build the reviewed STTM, data model, DQ rules, ER diagram, relevant design brief, and
explicitly accepted gaps/waivers — nothing from `00_state/`.

At a terminal run state (`completed`, `cancelled`, or unrecoverable `error`), nothing is
deleted: `inputs/`, `outputs/00_state/` (including `runtime_scratch/`), and `outputs/` are
all preserved.

## `memory/` — durable operational learnings

```text
memory/
  README.md
  MEMORY.md            reusable facts, project-agnostic conventions
  CONVENTIONS.md        writing, naming, formatting, delivery conventions
  DECISIONS.md          decisions that should persist across runs
  PATTERN_LIBRARY.md     high-value reusable section or artifact patterns
```

Read once at the start of a run, written back only at the `/evaluate-design` closure tail
when a durable, reusable, human-validated learning is confirmed. Client data, raw extracts,
generated artifact contents, PII/PHI, and unapproved business rules never belong here — see
[Configuration](../reference/configuration.md) for the full governance rule.

## `config/` — package defaults

`config/project_config.json` holds naming patterns, layer prefixes, standard audit
columns, default DQ check thresholds, and the folder/contract paths every phase skill
reads. See [Configuration](../reference/configuration.md) for its contents.

## Next

See [Command reference](../how-to-run/command-reference.md) for what each phase reads and
writes, or [Revisions and recovery](revisions-and-recovery.md) for how to fix a wrong
value after a phase has already run.
