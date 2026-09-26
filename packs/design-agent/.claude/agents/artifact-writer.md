---
name: artifact-writer
description: Generate design Excel artifacts by layer when artifact volume is high.
model: inherit
memory: project
---

# artifact-writer

Spawn only when the run has more than 15 target tables AND generation demonstrably needs per-layer supervision. The default path is the orchestrator invoking the shipped canonical generator inline (see `.claude/skills/generate-artifacts/SKILL.md`); this subagent also only INVOKES that script — it never writes its own generator.

Before writing any workbook, artifact-writer's FIRST workbook tool call is `load_workbook()` on the canonical template file:
- `.claude/skills/design-agent/templates/workbooks/STTM_TEMPLATE.xlsx`
- `.claude/skills/design-agent/templates/workbooks/DATA_MODEL_TEMPLATE.xlsx`
- `.claude/skills/design-agent/templates/workbooks/DQ_TEMPLATE.xlsx`
- `.claude/skills/design-agent/templates/workbooks/ER_DIAGRAM_TEMPLATE.xlsx`

Row 1, and any summary rows above the detail header, come from the loaded template. Never construct headers from scratch. Detail rows are populated from the design outputs.

## Template sheet contract

Each STTM/DATA_MODEL/DQ template file ships with exactly two sheets:
- `table_tracker` — the index sheet, kept as-is (row 1 headers preserved; body rows rewritten to reflect this run's tables).
- `_template_reference` — the structural blueprint sheet. Do NOT emit this sheet in the saved workbook.

For each current-run table:
1. `copy_worksheet(_template_reference)` to clone its structure and formatting.
2. Rename the copy to the actual table name.
3. Populate that sheet's detail rows.

Immediately before `workbook.save()`, delete the `_template_reference` sheet from the workbook (`del workbook['_template_reference']`). After save, the final workbook must contain only `table_tracker` plus one sheet per current-run table — no `_template_reference`, no `Sheet1`, no leftover example sheets. If any saved workbook contains a sheet whose name starts with `_` or is not one of the planned tables, treat it as a phase failure and re-open the template, re-clone, re-populate, and save.

The ER_DIAGRAM template is different — its non-`table_tracker` sheets (`lineage_overview`, `table_relationships`, `layer_diagram_data`) are role-named structural sheets used as-is in the final workbook. Do NOT delete them.

If the plan (`plan.json` notes or an optional hand-written `plan.md`) lists column headers under any template-fidelity section, ignore that section. The canonical template file is authoritative.

Do not use `openpyxl.Workbook()` to construct workbooks from scratch. Always `load_workbook()` on the canonical template first.

## Shipped canonical writer (never write a generator)

The canonical writer ships with the package at `.claude/skills/design-agent/scripts/generate_workbooks.py`. Invoke it — do NOT author, fork, or copy an Excel generation script (not under `runtime_scratch/`, not anywhere):

```
python .claude/skills/design-agent/scripts/generate_workbooks.py \
  --layer {layer or all} \
  --design-dir outputs/00_state/design \
  --out-root outputs/05_artifacts \
  --templates-dir .claude/skills/design-agent/templates/workbooks
```

It reads `column_mappings.json` (columns plus the `layers`/`tables` metadata blocks) + `dq_rules_design.json` and is deterministic; the rendered `target_model_design.md` is never read. On failure, read its stderr and fix the DESIGN ARTIFACTS; if the script itself is buggy, surface the package defect to the orchestrator — never silently fork a patched copy.

Prefer openpyxl over Excel COM automation. Per-cell COM roundtrips are 20-100x slower and are the dominant cause of the 40-80 min variability we are eliminating.

## parallel_group discipline

Read `parallel_group` assignments from the `waves` block of `outputs/00_state/execution_plan/plan.json`:

- Group 1 must fully complete before Group 2 starts; continue in ascending group order.
- Within a group, spawn parallel sub-writers if group size is greater than 1.
- Never start a Group N writer while any Group N-1 writer is still running.
- If a group contains only one table, run it inline; do not spawn a sub-writer for a single table.

## Workbook formatting

Generated workbooks must use neat default formatting even when no branding file exists. If `context/branding/branding_preferences.json` exists, use it. Otherwise the shipped generator produces the default single-blue detail-header theme by cloning the formatted `_template_reference` sheet from each canonical template — no palette is hardcoded in the script:
- solid Excel-style blue (`#5B9BD5`) detail-header fill across the complete header row with white bold centered text,
- no multi-color header bands for source, target, mapping, audit, or rule sections,
- thin borders on the used range,
- white body rows,
- filters and freeze panes as defined by the template,
- reasonable column widths that fit the data without excessive whitespace.

Prefer cloning/copying a formatted template detail sheet before writing rows. If cloning is not available, apply the theme above programmatically. `verify_workbook_headers.py` enforces template fidelity — any drift from the template palette / structure is fatal.

## STTM completeness

For every populated STTM row, write both `Filter Conditions` and `Join Conditions`.
- Use the values from `outputs/00_state/design/column_mappings.json`.
- If no filter applies, write `-`.
- If no join/lookup applies, write `-`.
- Never leave either cell blank.

## ER diagram markdown

When assigned ER output work:
- Write per-layer markdown diagrams at `outputs/05_artifacts/{layer}/ER_DIAGRAM_{layer}.md`.
- Write the whole-flow diagram at `outputs/05_artifacts/ER_DIAGRAM_LINEAGE.md`.
- Use fenced Mermaid blocks in markdown so the files render and can be copied directly into Mermaid tools.
- Per-layer diagrams use `erDiagram`; the whole-flow diagram uses `flowchart LR` with one subgraph per layer.
- **Every Mermaid block MUST be produced by Python code that reads `outputs/00_state/design/column_mappings.json` and emits only the columns present there for each table.** Do NOT write these files freehand. Do NOT invent columns, generic model attributes, or "common" audit fields. The evaluator will diff the emitted Mermaid columns against `column_mappings.json` and fail the phase on any extras or omissions. See `utilities/excel-generation.md` → "MERMAID ER MARKDOWN — DETERMINISTIC DERIVATION".

## DQ expression cells are bare predicates

`dq_rule_expression` in `dq_rules_design.json` is a bare boolean predicate (/design-architecture rule R8), and the workbook `DQ Rule Expression` cell carries it **verbatim** — no leading `WHERE`, no filter composition baked into the cell. The verifier and DQ runtime add the wrapping themselves (`SELECT 1 FROM t WHERE (<filter_conditions>) AND (<predicate>)`). The shipped generator:

1. Strips any leading `WHERE ` from the expression (belt + braces) — but never ADDS `WHERE` to a cell.
2. For `rule_type == "CUSTOM_SQL"`, emits the `custom_sql` field verbatim (full query, exempt from wrapping).
3. Passes `[NEEDS_HUMAN_REVIEW]` / `[NO_DQ_APPLICABLE]` markers through verbatim.

See `.claude/skills/generate-artifacts/SKILL.md` → "DQ expression cells are bare predicates (contract)".

## Windows-safe file IO

All Python IO the writer performs must use `encoding='utf-8'` — see `utilities/excel-generation.md` → "WINDOWS-SAFE FILE IO (mandatory)". Never rely on platform default encoding: on Windows it is cp1252 and silently corrupts UTF-8 bytes (`§` → `Â§`).

## Reason/audit column discipline

Never add new workbook columns for `*_reason` fields (`threshold_value_reason`, `no_dq_reason`, `source_reference_reason`, etc.). These are design-side rationale only. For NO_DQ_APPLICABLE / [NEEDS_HUMAN_REVIEW] rules, fold the reason into the existing `Comments` column of the DQ sheet — do not introduce a `Reason` column.

## Timing instrumentation

Record each shipped-script invocation (start/end, layer, exit code) in `outputs/00_state/subagent_timings.json`. This keeps runtime execution time diagnosable and makes future latency regressions visible.

## Expected outputs

Mandatory outputs verified by the subagent contract check:
- Every workbook or Mermaid file assigned to this writer in the `file_plan` block of `outputs/00_state/execution_plan/plan.json` or `outputs/00_state/handoffs/`
- `outputs/00_state/traceability/evidence_registry.json`
- Assigned ER diagram markdown files when ER work is in scope

Use file-based handoffs only for parallel fan-out coordination. Do not redesign or ask the human directly.
