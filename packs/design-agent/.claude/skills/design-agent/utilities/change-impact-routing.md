# CHANGE IMPACT ROUTING POLICY

## Purpose

Human feedback can range from a typo to a fundamental source/design change, and it can arrive at any phase boundary or after evaluation. The orchestrator must route each requested change to the earliest phase that owns the decision, then re-run all downstream phases needed to keep artifacts consistent.

## Bulk feedback first

When the human requests changes, ask for the complete change list in one batch when possible. Multiple small changes may combine into a deeper rollback need.

## Earliest-phase routing matrix

| Change type | Examples | Earliest phase to re-run | Downstream work required |
|---|---|---|---|
| Cosmetic/output formatting only | widths, labels, workbook presentation, typo in comments with no design meaning | /generate-artifacts | Regenerate/patch affected outputs, then re-run /evaluate-design |
| Output population bug | missing References, wrong row order, template dummy data left, generated value not matching approved design | /generate-artifacts | Regenerate affected artifacts, update manifests, re-run /evaluate-design |
| Execution plan/file structure | add/remove planned workbook, wrong layer file list, dependency order issue | /design-architecture (plan step) | Re-run the /design-architecture planner, then /generate-artifacts, /evaluate-design |
| Architecture/design change | add/remove table/column, change grain, PK/FK, source-to-target mapping, transformation, DQ rule, layer assignment | /design-architecture | Re-run /design-architecture (design + plan), /generate-artifacts, /evaluate-design |
| Source selection change | use different source, add a missing source, reject a previously selected source | /start-design (source-discovery step) | Re-run the /start-design source decisions, then /design-architecture, /generate-artifacts, /evaluate-design |
| Standard input change | new/changed BRD, source inventory, KPI formula, business rule, context hierarchy decision, user instruction | /start-design | Re-ingest/re-index the updated evidence, then re-run downstream phases as needed |
| Foundational run setup/input snapshot issue | files missing from snapshot, wrong input category, invalid run scaffold | /start-design | Rebuild snapshot/parse, then re-run downstream phases as needed |

## Consistency rule

A change to one artifact often requires synchronized updates to others. For example, changing a target column requires STTM, Data Model, DQ, ER Diagram, design artifacts, execution plan, validation logs, and traceability registry updates where applicable.

## Feedback log

Record every item in `outputs/00_state/human_review/human_review_feedback.json` with:

- feedback ID and raw user text;
- classification;
- earliest phase required;
- affected artifacts/tables/columns;
- cascade impacts;
- files regenerated/updated;
- post-change validation results;
- whether the issue should become a learning captured by the evaluate-design closure tail.
