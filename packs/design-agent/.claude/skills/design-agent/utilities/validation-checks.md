# VALIDATION CHECKS

These checks are used during /generate-artifacts execution and /evaluate-design evaluation. /generate-artifacts performs incremental validation while generating artifacts. /evaluate-design performs full deterministic validation as a blocking check.

## PRE-TABLE VALIDATION

Run before generating any artifact for a table.

Checks:

1. Table exists in the approved design (`column_mappings.json` `tables` block).
2. Table appears in the approved `outputs/00_state/execution_plan/plan.json` (`waves` + `file_plan` blocks).
3. Source tables referenced by this table exist in one of:
   - `source_decisions.json` entries with `status: "selected"` for L0 only,
   - prior-layer approved outputs/design,
   - explicitly human-approved external source exception.
4. L1+ mappings do not read directly from unselected external sources.
5. Source columns exist in their source metadata or prior-layer design.
6. Transformation logic is non-empty and specific.
7. Every mapping has grounding and planned row-level references: `source_direct`, `business_rule`, `human_input`, `standard_pattern`, `derived`, or `best_guess`.
8. `best_guess` appears only when the human explicitly chose to proceed with documented risks and the item exists in the risk manifest.
9. Data types are specified for every output column.
10. `surrogate_key` and `audit` columns have no external source unless explicitly approved.
11. Business keys are nullable = `N` unless explicitly waived.
12. No same-layer physical transformation dependency exists unless documented as an explicitly human-approved design exception.

If any non-risk-manifest critical check fails, STOP. Do not silently invent a fix in /generate-artifacts.

## POST-TABLE VALIDATION

Run after generating Data Model, STTM, and DQ for a table.

Checks:

1. STTM Target Columns equal Data Model Attribute Names for the table.
2. STTM Target Data Types equal Data Model Data Types for each column.
3. STTM Roles equal Data Model Roles for each column.
4. STTM Target Nullable equals Data Model Nullable for each column.
5. STTM Primary Key equals Data Model Primary Key for each column.
6. DQ Column Names are a subset of Data Model Attribute Names.
7. DQ Data Types match Data Model Data Types.
8. Every business_key column has a DQ `Not NULL` check unless waived.
9. Every primary key has a DQ `Uniqueness` check unless waived.
10. Every FK/lookup column has a DQ `Referential Integrity` check unless waived.
11. Summary values (Layer, Table Name, Description, Schema, Database) are consistent across all 3 artifacts.
12. `[BEST-GUESS]` comments align with the risk manifest.
13. Every populated STTM/Data Model/DQ detail row has a non-empty `References` cell.

If mismatch is caused by generation error, fix immediately. If mismatch reveals an approved design problem, stop and route back to the phase that owns the decision (see change-impact-routing.md).

## POST-LAYER VALIDATION

Run after completing all tables in a layer and saving workbooks.

Checks:

1. All tables from the `column_mappings.json` `tables` block for this layer are present.
2. Each layer has exactly 3 workbooks: STTM, DATA_MODEL, DQ.
3. Each workbook has `table_tracker` plus one sheet per table in that layer.
4. `table_tracker` rows match workbook sheet names.
5. No sheets from other layers appear.
6. All 3 workbooks are readable and non-empty.
7. FK references point to existing tables/columns.
8. No unapproved same-layer physical dependency appears in lineage or STTM join logic.

## FINAL CROSS-LAYER VALIDATION

Run after all layers and ER Diagram are generated.

Checks:

1. All layer output folders exist in `outputs/`.
2. Each layer folder has exactly 3 Excel files.
3. `ER_DIAGRAM.xlsx` exists once at `outputs/ER_DIAGRAM.xlsx`.
4. ER `lineage_overview` covers all approved tables.
5. ER `table_relationships` references existing table.column values only.
6. STTM/Data Model/DQ names and data types are consistent.
7. STTM lineage agrees with approved lineage traces.
8. Every selected source has an L0 table unless explicitly waived.
9. No unselected source is used downstream unless human-approved.
10. Total Excel file count equals `(num_layers * 3) + 1`.
11. If the human chose to proceed with documented risks, `outputs/RISK_MANIFEST.json` exists and covers every `[BEST-GUESS]` item.
12. Otherwise, no `[BEST-GUESS]` appears anywhere.
13. No Excel artifact exists directly under `outputs/` root; all current-run deliverables are under `outputs/`, and previous run folders remain untouched.
14. No generated runtime scripts exist in `inputs/`, `outputs/`, `.claude/skills/design-agent/`, `.claude/`, `.claude/skills/design-agent/templates/workbooks/`, `config/`, `context/reference/`, `memory/`, or project root. Runtime code, if any, is contained under `outputs/00_state/runtime_scratch/`.
15. No dummy/example/prototype data remains in any output workbook.
16. Every populated STTM/Data Model/DQ detail row has a non-empty `References` cell.

## INPUT SET VALIDATION

Input standardization validation checks:

1. `outputs/00_state/standard_input_set/input_set_evaluation_report.md` exists before any 02 - Standardize_Inputs human clarification is recorded.
2. All four context components exist (even if empty/low confidence): `enterprise_context.json`, `domain_context.json`, `project_context.json`, `user_instructions.json`.
3. `source_inventory.json` is explicitly marked as the full source universe, not selected sources.
4. `dq_requirements.json` and `additional_documents.json` exist and are indexed.
5. Any file added to `inputs/midrun_uploads/` during clarification is copied to `outputs/00_state/midrun_uploads/`, parsed, logged, and applied or rejected with reason.
6. Unsupported or failed-parse files are listed in the report and not silently ignored.
7. All human answers after report generation are recorded in the canonical `outputs/00_state/standard_input_set/human_clarifications.json`.
8. All `inputs/instructions/user_instructions.*` files and clearly directive context files are parsed into `user_instructions.json` and never lumped into enterprise/domain/project context.
9. Every conflict between any two context tiers identified in `input_set_evaluation_report.md` Section 4B has a corresponding clarification answer in `outputs/00_state/standard_input_set/human_clarifications.json`. No silent overrides.

## USER INSTRUCTIONS APPLICATION VALIDATION

Run after every stage that may apply user-instruction directives (02 - Standardize_Inputs, 03 - Discover_Sources, 04 - Design, 05 - Plan, 06 - Execute).

For each directive in `outputs/00_state/standard_input_set/user_instructions.json`:

1. Status must be one of: `pending` (only valid before final stage), `applied`, `deferred_with_confirmation`, `rejected_with_confirmation`.
2. Status `unaddressed` is forbidden — if the agent cannot address a directive, it must be explicitly flagged as deferred or rejected with confirmation, not silently ignored.
3. `applied` directives have non-empty `evidence` (a file:cell or design decision reference).
4. `deferred_with_confirmation` and `rejected_with_confirmation` directives have a non-null `human_confirmation_id` and `status_reason`.
5. Counters in `outputs/00_state/run_state.json.user_instructions` and inside `outputs/00_state/standard_input_set/user_instructions.json` agree with directive statuses.
6. By the end of 06 - Execute, no directive should remain `pending`.

## CONTEXT HIERARCHY VALIDATION

Run after 02 - Standardize_Inputs and re-run at 08 - Evaluate.

For every conflict identified between any two context tiers:

1. The conflict has a recorded `severity` (`normal | elevated | high`) per the tier-distance rule.
2. The conflict has a corresponding clarification answer in `outputs/00_state/standard_input_set/human_clarifications.json` with `applied_decision`.
3. The output (design, plan, generated artifacts) reflects the confirmed decision.
4. `outputs/00_state/run_state.json.context_overrides.all_overrides_confirmed` is `true`.

## TEMPLATE-SHAPE VALIDATION

Default strictness is content-strict and format-reasonable.

### STTM

- Summary rows 1-7.
- Row 1: `SOURCE TO TARGET - SUMMARY`.
- Row 8: `SOURCE TO TARGET - DETAILS`.
- Row 9 headers, 17 columns:
  `Target Table`, `Target Column`, `Role`, `Target Data Type`, `Target Nullable`, `Source Table`, `Source Column`, `Source Data Type`, `Transformation Logic`, `Filter Conditions`, `Join Conditions`, `Column Description`, `Primary Key`, `Schema Name`, `Database Name`, `References`, `Comments`.

### Data Model

- Summary rows 1-7.
- Row 1: `DATA MODEL - SUMMARY`.
- Row 8: `DATA MODEL - DETAILS`.
- Row 9 headers, 14 columns:
  `S.No.`, `Schema Name`, `Database Name`, `Table Name`, `Logical Name`, `Attribute Name`, `Data Type`, `Role`, `Nullable`, `Primary Key`, `Column Description`, `Ordinal Position`, `References`, `Comments`.

### DQ

- Summary rows 1-6.
- Row 1: `DQ - SUMMARY`.
- Row 3 label must be `Table Name`, not `Staging Table Name`.
- Row 7: `DQ - DETAILS`.
- Row 8 headers, 12 columns:
  `S.No.`, `Schema Name`, `Database Name`, `Table Name`, `Column Name`, `Data Type`, `DQ Check`, `DQ Rule Expression`, `Criticality`, `Threshold Value`, `References`, `Comments`.

### ER Diagram

- Required template: `.claude/skills/design-agent/templates/workbooks/ER_DIAGRAM_TEMPLATE.xlsx`.
- Required sheets: `table_tracker`, `lineage_overview`, `table_relationships`, `layer_diagram_data`.
- Required columns follow `.claude/skills/design-agent/templates/specs/er-diagram-spec.md` and `.claude/skills/design-agent/specs/template_contracts.yaml`, including ER `References` headers added to the canonical template.
- Do not generate an ad hoc ER workbook if the template is missing or incompatible; report a template defect.

## VALIDATION LOG

All validation results should be logged in `outputs/00_state/validation_log.json`:

```json
{
  "validations": [
    {
      "type": "pre_table | post_table | post_layer | final_cross_layer | template_shape | deterministic_s9",
      "layer": "L2",
      "table": "f_trn",
      "timestamp": "2026-05-19T15:30:45+05:30",
      "passed": true,
      "critical": false,
      "checks_run": 12,
      "checks_passed": 12,
      "issues": [],
      "risk_manifest_ids": [],
      "resolution": null
    }
  ]
}
```

08 - Evaluate consumes this log but must not rely on it blindly; 08 - Evaluate should independently re-check critical deterministic validations.


## TRACEABILITY VALIDATION

Run during /generate-artifacts focused checks and /evaluate-design full evaluation.

Checks:

1. `outputs/00_state/traceability/evidence_registry.json` exists.
2. Every populated STTM detail row has non-empty References.
3. Every populated Data Model detail row has non-empty References.
4. Every populated DQ detail row has non-empty References.
5. Reference tokens use allowed prefixes from `.claude/skills/design-agent/utilities/traceability-reference-policy.md` or are recorded in the evidence registry.
6. `INFERRED-*` references are paired with supporting evidence.
7. `[BEST-GUESS]` rows reference a `RISK-*` item in the risk manifest.
8. Blank References on populated rows are critical failures.
