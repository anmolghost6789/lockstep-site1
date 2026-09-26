---
name: design-evaluator
description: Evaluate generated design outputs with deterministic checks and semantic scoring in one pass.
model: inherit
memory: project
---

# design-evaluator

Always spawn for /evaluate-design.

Read generated artifacts from disk, run deterministic checks and semantic scoring in one pass, and write outputs/00_state/evaluation/evaluation_report.md (rendered per .claude/skills/design-agent/references/report_grammar.md — the output evaluation report spine §5 — using the filled skeleton at .claude/skills/design-agent/references/OUTPUT_EVALUATION_REPORT.template.md) plus outputs/00_state/evaluation/evaluation_scores.json. Return a bounded in-context summary. Do not create separate deterministic or semantic reports.

## Mandatory inputs from the orchestrator

Before the evaluator does anything else, the orchestrator will have produced two deterministic reports at:

- `outputs/00_state/evaluation/header_check.json` (from `verify_workbook_headers.py`)
- `outputs/00_state/evaluation/semantic_check.json` (from `verify_artifact_semantics.py`)

The evaluator MUST:

1. Load both JSONs before scoring anything.
2. Treat every entry in `semantic_check.json.checks.dq_sql.errors` as a hard defect in `dq_quality` — cap that category at 6 regardless of narrative quality.
3. Treat every entry in `semantic_check.json.checks.er_mermaid.errors` as a hard defect in `lineage_quality` — cap at 6.
4. Treat every entry in `semantic_check.json.checks.encoding.errors` as a hard defect in `source_faithfulness` — cap at 6.
5. Independently scan every generated artifact (STTM, Data Model, DQ, and ER Diagram workbooks, plus `column_mappings.json` and `dq_rules_design.json`) against `.claude/skills/design-agent/knowledge/naming-conventions.md`, `layering-logic.md`, and `dq-patterns.md`. Treat any violation as a hard defect in `standards_conformance` — cap that category at 6 regardless of narrative quality. Violations include (non-exhaustive): a table/column/schema name that does not follow the documented pattern for its layer (e.g. an L2 dimension not prefixed `d_`, an L1 table missing the client/layer prefix, a column not in UPPER_SNAKE_CASE), a table placed in a layer that breaks a layering-logic.md rule (missing required L0 mirror, same-height violation, an undocumented same-layer physical dependency), or a DQ rule set that omits a check `dq-patterns.md` mandates for that column's role (e.g. no Uniqueness check on a surrogate key, no Not NULL check on a business key, no Referential Integrity check on an FK column). This check has no dedicated Python script the way the three checks above do — the evaluator performs it directly against the knowledge files as part of this pass — but it is held to the same rigor: cite the concrete file/table/column for every violation, do not judge conformance narratively.
6. Cite the concrete files/rows/tables from those reports, and from the standards-conformance scan, in the evaluation report; do not paraphrase.
7. NEVER recommend `APPROVE` while `semantic_check.json.passed == false` or `header_check.json.passed == false`, or while any standards-conformance violation remains unresolved. Use `NEEDS_REVISION` and route back to the correct phase (design for schema/layering issues, generate-artifacts for composition/encoding/naming issues).

The three scripted checks encode general invariants that content inspection can verify but LLM scoring cannot: **DQ SQL validity** (every rule expression must parse as SQL), **ER Mermaid ⊆ design columns** (diagrams cannot claim columns the design does not have), and **encoding cleanliness** (workbook cells and design JSONs must be free of UTF-8→cp1252 corruption). Deterministic tools verify these three invariants; the evaluator's job is to fold their findings into scoring and the recommendation. The fourth check, **standards conformance** (naming, layering, and DQ-pattern rules are followed, not just invoked), is likewise deterministic in nature — it is a pattern-match against documented rules, not a subjective read — but is evaluator-performed rather than script-backed today.
