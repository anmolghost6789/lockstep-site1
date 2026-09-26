# Input Files

Place your project documents in the appropriate subfolders below. The agent classifies files by content, not by filename — so placing them in the right folder helps organization but is not strictly required.

**More input = better output.** The agent produces everything it can from whatever you provide. Missing inputs result in documented assumptions or `[INSUFFICIENT INPUT]` notices in the output.

## Folder Structure

### `sttm/`
Source-to-target mapping files. The golden template (`templates/STTM_TEMPLATE.xlsx`) provides optimal structure, but any mapping format works.

### `data_model/`
Data model documentation, relationship definitions, entity-relationship diagrams. The golden template (`templates/DATA_MODEL_TEMPLATE.xlsx`) is recommended.

### `dq_rules/`
Data quality rules and validation specifications. The golden template (`templates/DQ_RULES_TEMPLATE.xlsx`) is recommended.

### `context/`
Context documents:
- **Enterprise context** — org structure, SQL dialect, DQ framework, compliance policies
- **Domain context** — industry terminology, data patterns
- **Project context** — specific project scope, timeline, tech stack

### `business_rules/`
Business rules, transformation logic, calculation specifications, domain-specific formulas.

### `legacy_code/`
Legacy SQL, reference code, stored procedures, existing ETL scripts. Helps the agent understand existing patterns.

### `reference/`
Any additional supporting material: known gaps, user instructions, coding standards, architecture docs.

## Tips
- The agent reads DOCX, PDF, TXT, MD, XLSX, PPTX, JSON, CSV, and SQL files
- Template files in `templates/` show the ideal structure but are not required
- Template-conformant inputs produce higher-confidence outputs
