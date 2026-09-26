# How to Use Templates

## Overview

The Build Agent works with whatever inputs you have. Templates define the optimal input structure for highest-confidence parsing. Template conformance is a confidence accelerator, never a requirement.

## Input Organization

Place your files in the appropriate subfolder under `inputs/`:

| Folder | What goes here |
|--------|---------------|
| `inputs/sttm/` | Source-to-target mapping files |
| `inputs/data_model/` | Data model, relationship documentation |
| `inputs/dq_rules/` | Data quality rule definitions |
| `inputs/context/` | Enterprise/domain/project context, user instructions, business rules, known gaps |
| `inputs/legacy_code/` | Existing SQL, stored procedures, reference code |
| `inputs/additional_documents/` | Any other supporting material |

You can also put everything in `inputs/` directly — the agent reads recursively and classifies by content.

## Golden Templates

### STTM_TEMPLATE.xlsx
Optimal format: `table_tracker` sheet with table-level metadata, per-table sheets with summary block (rows 1-10) and detail block (column mappings).

### DATA_MODEL_TEMPLATE.xlsx
Optimal format: `table_tracker` sheet, `relationships` sheet (From/To columns), per-table sheets.

### DQ_RULES_TEMPLATE.xlsx
Optimal format: `table_tracker` sheet, per-table sheets with DQ Check, Expression, Criticality (C/NC), Threshold columns.

### Context templates
- `enterprise_context.md` — SQL dialect, naming conventions, org standards
- `domain_context.md` — industry terminology
- `project_context.md` — scope, timeline, tech stack
- `user_instructions.md` — delivery preferences, must-follow rules
- `business_rules.md` — transformation and derivation logic
- `known_gaps.md` — documented issues, open questions

## What Happens Without Templates

The agent still works. It uses content-based classification and best-effort parsing. Confidence may be lower for non-template inputs, and more assumptions may be needed. The Input Evaluation Report will tell you exactly what was found and what confidence to expect.

## What Improves Output Quality

| Input | Effect |
|-------|--------|
| Complete STTM with all columns mapped | Full DDL and DML generation, high confidence |
| Data model with relationships | Correct dependency ordering, join logic |
| DQ rules with expressions | Complete DQ artifacts (not just stubs) |
| Enterprise context with SQL dialect | Correct syntax for target platform |
| Business rules with derivation logic | Accurate transformation implementation |
| Legacy code | Pattern evidence for complex transforms |
