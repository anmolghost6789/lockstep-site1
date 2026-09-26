# Overview

## What Design Agent is

Design Agent is the second stage of the data-engineering delivery lifecycle:

```text
Requirements -> Design -> Build -> Deploy -> Test
```

It turns approved business requirements and available source-system evidence into the
design artifacts an engineering team needs before implementation begins:

- a **source-to-target mapping (STTM)** per data-model layer,
- a **layered data-model workbook** per layer,
- a **data-quality (DQ) rules workbook** per layer,
- an **ER diagram** (workbook plus Mermaid markdown, per layer and whole-flow).

The package records the design as canonical facts first — column mappings and DQ rules in
two JSON files — and then generates every human-readable workbook, diagram, and review
document from those facts with deterministic scripts. See
[Design facts before files](../workflow/phases.md#design-facts-before-files) for why this
matters.

## What Design owns and what it does not

| Design owns | Design does not own |
|---|---|
| Source selection, target structure, mappings, lineage, DQ rules, and artifact generation. | Inventing missing source facts, writing production DDL/DML, deploying pipelines, or executing production tests. |
| Transparent gap and waiver handling. | Treating a template as evidence or silently replacing a source decision. |
| STTM, data model, DQ, and ER deliverables. | Making business-scope decisions that belong in Requirements. |

Use Design after Requirements has established business scope, behavior, and key data
needs. Use Build after Design has produced, and a human has reviewed, the mappings and
target model — Build turns the reviewed STTM and data model into DDL/DML, DQ checks, and
pipeline orchestration; Design never writes that implementation code itself.

## Where Design sits in the lifecycle

| Stage | Package | Consumes from Design | Produces |
|---|---|---|---|
| Requirements | `requirements-skill-package` | — | BRD, FRD, URS, Jira Story Pack |
| **Design** | `design-skill-package` | Reviewed BRD/FRD, source inventory | STTM, data model, DQ workbook, ER diagram |
| Build | `build-skill-package` | Reviewed STTM, data model, DQ rules | DDL, DML, DQ checks, pipeline configuration |
| Deploy | `deploy-skill-package` | Reviewed Build output | PR body, deployment plan, audit trail |
| Test | `test-skill-package` | Deployed solution | Evidence-backed tests, results, test report |

## Key concepts

- **Canonical facts, rendered views.** `outputs/00_state/design/column_mappings.json` and
  `dq_rules_design.json` are the single source of truth for every mapping and DQ rule. The
  review markdown (`target_model_design.md`), the execution plan (`plan.json`), the
  workbooks, and the ER diagrams are all produced by shipped scripts from those two files —
  never hand-typed twice.
- **Phase boundaries, no auto-chaining.** Each slash command is a checkpoint: it writes its
  outputs and state, recommends the next command, and stops. The user invoking the next
  command is the approval to continue.
- **Layered target model.** Design always includes an always-on raw layer (L0), typically
  followed by a staging/conformed layer (L1) and a dimensional layer (L2), with prefixes
  such as `d_` (dimension), `f_` (fact), `ref_` (reference), and `xref_` (cross-reference).
  See [Configuration](../reference/configuration.md) for the full naming and layering
  defaults.
- **Source selection integrity.** `/design-architecture` designs only from sources marked
  `status: "selected"` in `source_decisions.json` (plus explicit waivers) — it never
  re-discovers or silently substitutes a source.
- **Traceability.** Every populated STTM/data-model/DQ row carries a non-empty
  `References` value pointing back to the evidence it came from.

## Main outputs

| Output | File(s) | Produced by |
|---|---|---|
| STTM | `outputs/05_artifacts/{layer}/STTM_{layer}.xlsx` | `/generate-artifacts` |
| Data model | `outputs/05_artifacts/{layer}/DATA_MODEL_{layer}.xlsx` | `/generate-artifacts` |
| DQ workbook | `outputs/05_artifacts/{layer}/DQ_{layer}.xlsx` | `/generate-artifacts` |
| ER diagram | `outputs/05_artifacts/ER_DIAGRAM.xlsx`, per-layer and whole-flow Mermaid `.md` files | `/generate-artifacts` |
| Design brief and review markdown | `outputs/03_design/design_brief.md`, `target_model_design.md` | `/design-architecture` |
| Evaluation report | `outputs/06_evaluation/evaluation_report.md` | `/evaluate-design` |

## Next

Read [Prerequisites](prerequisites.md) to set up Claude Code for this package, then
[Quick start](quick-start.md) for the fastest path to a first run.
