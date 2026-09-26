`outputs/` is the single working tree for a run. There is no per-run output
folder and no mirror/publish step — the agent writes each user-facing deliverable directly
into its numbered phase folder at the phase boundary, and keeps agent-internal run state under
`outputs/00_state/`. Design uses numbered phase folders:

```
outputs/
  00_state/         agent-internal run state (run_state.json, input_snapshot/, context_snapshot/,
                    runtime_scratch/, source_discovery/, design/, execution_plan/, handoffs/,
                    traceability/, logs/, evaluation/) — never a deliverable
  01_inputs/        input_set_evaluation_report.md
  02_sources/       source_selection_decisions.json, selected_sources.json, source_gap_report.md
  03_design/        design_brief.md, column_mappings.json, target_model_design.md
  04_plan/          plan.md, file_plan.json, generation_order.json
  05_artifacts/     {layer}/STTM_{layer}.xlsx, {layer}/DATA_MODEL_{layer}.xlsx, {layer}/DQ_{layer}.xlsx, ER_DIAGRAM.xlsx
  RISK_MANIFEST.json  (at outputs root, only if force-continue was used)
  06_evaluation/    evaluation_report.md, deterministic_validation_report.md, semantic_judge_report.json
```

Phase-to-destination table (working copy in `outputs/00_state/`, published deliverable in the
numbered folder):

| Phase/stage | Working copy (`outputs/00_state/`) | Published deliverable |
|---|---|---|
| `02-standardize-inputs` | `outputs/00_state/standard_input_set/input_set_evaluation_report.md` | `outputs/01_inputs/input_set_evaluation_report.md` |
| `03-discover-sources` | `outputs/00_state/source_discovery/source_selection_decisions.json`, `selected_sources.json`, `source_gap_report.md` | `outputs/02_sources/` |
| `04-design` | `outputs/00_state/design/design_brief.md` (or `target_model_design.md`), `column_mappings.json` | `outputs/03_design/` |
| `05-plan` | `outputs/00_state/execution_plan/plan.md`, `file_plan.json`, `generation_order.json` | `outputs/04_plan/` |
| `06-execute` | workbooks generated directly | `outputs/05_artifacts/{layer}/` |
| `06-execute` | `ER_DIAGRAM.xlsx` | `outputs/05_artifacts/` |
| `06-execute` | `RISK_MANIFEST.json` (if force-continue) | `outputs/RISK_MANIFEST.json` |
| `08-evaluate` | `outputs/00_state/evaluation/` reports | `outputs/06_evaluation/` |

Agent-internal state that never becomes a deliverable stays under `outputs/00_state/`:
`run_state.json`, `progress.json` (at the run root), `runtime_scratch/`, `handoffs/`, plus
durable cross-run material under top-level `memory/`.

After writing or copying user-facing artifacts, update the run-root `progress.json`. If a
required output is missing, note it in the phase's final report.
