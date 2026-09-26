
# DQ CHECK TEMPLATE SPECIFICATION

## WORKBOOK STRUCTURE

Each DQ workbook is **per layer** and contains:
- Sheet 1: `table_tracker` (index of all tables)
- Sheet 2+: One sheet per target table (sheet name = table name in lowercase)


## SHEET: table_tracker

Same as STTM and Data Model: S. No., Table Name, Comments.


## TABLE SHEETS: Summary Section (Rows 1-6)

**NOTE:** DQ summary has 6 rows (not 7). No Frequency row. Uses "Table Name" in row 3.

| Row | Cols A-B (merged) | Col C onward (merged to L) |
|-----|-------------------|---------------------------|
| 1 | DQ - SUMMARY | (merged A1:L1) |
| 2 | Layer | Layer identifier |
| 3 | Table Name | Table name in UPPER_CASE |
| 4 | Table Description | Full description |
| 5 | Schema Name | Target schema |
| 6 | Database Name | Target database |

**Merged Cells:**
- A1:L1 (header)
- A{n}:B{n} for rows 2-6 (labels)
- C{n}:L{n} for rows 2-6 (values)


## TABLE SHEETS: Detail Section

| Row | Content |
|-----|---------|
| 7 | "DQ - DETAILS" (merged A7:L7) |
| 8 | Column headers (12 columns, A through L) |
| 9+ | Data rows — one per DQ check (one column can have multiple rows) |

### Detail Column Definitions (12 columns)

| Col | Header | Required | Description |
|-----|--------|----------|-------------|
| A | S.No. | Always | Sequential integer |
| B | Schema Name | Always | Target schema |
| C | Database Name | Always | Target database |
| D | Table Name | Always | Target table name (UPPER_CASE in DQ) |
| E | Column Name | Always | Column being checked |
| F | Data Type | Always | Column data type |
| G | DQ Check | Always | Check type name (see catalog below) |
| H | DQ Rule Expression | Optional | SQL-like expression. Blank if self-evident. |
| I | Criticality | Always | `C` (Critical) or `NC` (Non-Critical) |
| J | Threshold Value | Optional | Acceptable error percentage or threshold value. Use the corrected template spelling: "Threshold Value". |
| K | References | Always for populated detail rows | Row-level evidence references separated by `; `; must support the DQ rule basis. |
| L | Comments | Optional | Additional notes |

### IMPORTANT: Multiple DQ Checks Per Column

A single column CAN and SHOULD have multiple DQ check rows when applicable. For example, a YM (Year-Month) column would have:
- Row 1: Not NULL check (Criticality: C)
- Row 2: Year month check (Criticality: C)

A TIMESTAMP column would have:
- Row 1: Not Null (Criticality: NC for audit columns)
- Row 2: Date Format Check (Criticality: NC)

### DQ Check Catalog

| DQ Check Name | When to Apply | Default Criticality | Default Threshold |
|---------------|--------------|--------------------:|------------------:|
| Not NULL | Business key columns, required attribute columns | C | 10 |
| Not Null | Audit columns, non-key required fields | NC | 5 |
| Uniqueness | Primary key columns (surrogate keys) | C | 0 |
| Referential Integrity | Foreign key columns (SK lookups in fact tables) | C | 5 |
| Date Format Check | DATE and TIMESTAMP columns | NC | 10 |
| Year month check | Year-month format columns (YYYYMM pattern) | C | 10 |
| Range Check | Numeric columns with known valid ranges | NC | 15 |
| Pattern Check | Code columns with known patterns (e.g., 4-digit codes) | NC | 10 |
| Duplicate Check | Table-level: tables that should have unique records | C | 0 |
| Completeness Check | Columns expected to be populated for all records | NC | 20 |
| Consistency Check | Values must agree with related tables | C | 5 |

### Criticality Rules

- **C (Critical):** Check failure blocks data loading. Business keys, surrogate keys, primary keys, referential integrity.
- **NC (Non-Critical):** Check failure generates warning but does not block. Audit columns, format checks, completeness checks.

### Standard DQ Checks by Column Role

| Role | Automatic DQ Checks |
|------|-------------------|
| surrogate_key | Uniqueness (C, threshold 0) |
| business_key | Not NULL (C, threshold 10) |
| attribute (DATE/TIMESTAMP) | Date Format Check (NC, threshold 10) |
| attribute (YYYYMM pattern) | Not NULL (C, 10) + Year month check (C, 10) |
| attribute (FK/lookup) | Referential Integrity (C, threshold 5) |
| audit | Not Null (NC, threshold 5) |
| audit (TIMESTAMP) | Not Null (NC, 5) + Date Format Check (NC, 10) |


## CONSISTENCY WITH DATA MODEL AND STTM

- Every Column Name (col E) in DQ MUST exist in the Data Model Attribute Names for the same table
- DQ Data Types MUST match Data Model Data Types for the same columns
- DQ does NOT need to cover every column — only columns with applicable checks
- DQ references (col K) must match STTM/Data Model references for the same columns


## TRACEABILITY / REFERENCES REQUIREMENT

Every populated detail row must have a non-empty `References` cell. Use `.claude/skills/design-agent/utilities/traceability-reference-policy.md` for allowed prefixes and evidence-registry rules. Multiple references are separated with `; `. Rows generated from `config/project_config.json` defaults, such as audit columns or standard DQ rules, still require references such as `CONFIG-audit-columns` or `PKG-dq-patterns-business-key`.
