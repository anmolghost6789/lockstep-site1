
# STTM TEMPLATE SPECIFICATION

## WORKBOOK STRUCTURE

Each STTM workbook is **per layer** and contains:
- Sheet 1: `table_tracker` (index of all tables)
- Sheet 2+: One sheet per target table (sheet name = table name in lowercase)


## SHEET: table_tracker

| Column | Header | Content |
|--------|--------|---------|
| A | S. No. | Sequential integer starting at 1 |
| B | Table Name | Target table name (lowercase, must match a sheet name) |
| C | Comments | Optional notes (blank if none) |


## TABLE SHEETS: Summary Section (Rows 1-7)

| Row | Cols A-B (merged) | Cols C onward (merged to Q) | Notes |
|-----|-------------------|----------------------------|-------|
| 1 | SOURCE TO TARGET - SUMMARY | (merged A1:Q1) | Section header |
| 2 | Layer: | Layer identifier (e.g., "L0", "L1", "L2") | Merge A2:B2, merge C2:Q2 is NOT required — value in C2 |
| 3 | Table Description: | Full table description text | |
| 4 | Loading Strategy | "Full load", "Incremental", "Truncate Load", etc. | |
| 5 | Schema Name | Target schema name | |
| 6 | Database Name | Target database name (with {env} placeholder) | |
| 7 | Frequency | "Monthly", "Daily", "Weekly", etc. | |

**Merged Cells in Summary:**
- A1:Q1 (full width header)
- A2:B2, A3:B3, A4:B4, A5:B5, A6:B6, A7:B7 (label cells)
- I2:Q2, I3:Q3, I4:Q4, I5:Q5, I6:Q6, I7:Q7 (right side of value area — optional merge for visual alignment)


## TABLE SHEETS: Detail Section (Rows 8+)

| Row | Content |
|-----|---------|
| 8 | "SOURCE TO TARGET - DETAILS" (merged A8:Q8) |
| 9 | Column headers (17 columns, A through Q) |
| 10+ | Data rows — one row per target column |

### Detail Column Definitions (17 columns)

| Col | Header | Data Type | Required | Valid Values / Rules |
|-----|--------|-----------|----------|---------------------|
| A | Target Table | String | Always | Same for all rows in this sheet. Lowercase table name. |
| B | Target Column | String | Always | Column name. UPPER_SNAKE_CASE unless client convention differs. |
| C | Role | String | Always | One of: `surrogate_key`, `business_key`, `attribute`, `audit` |
| D | Target Data Type | String | Always | VARCHAR, INTEGER, FLOAT, TIMESTAMP, DATE, BOOLEAN, NUMBER, NUMBER(p,s), VARCHAR(n), etc. |
| E | Target Nullable | String | Always | `Y` or `N` |
| F | Source Table | String | Conditional | Source table name, or `-` if no source (SK, audit) |
| G | Source Column | String | Conditional | Source column name, or `-` if no source |
| H | Source Data Type | String | Conditional | Source column data type, or `-` if no source |
| I | Transformation Logic | String | Always | See Transformation Logic Rules below. Never empty. |
| J | Filter Conditions | String | Optional | WHERE clause or filter description. Blank if none. |
| K | Join Conditions | String | Optional | JOIN clause or join description. Blank if none. |
| L | Column Description | String | Always | Format: "Description text\nSample Data: example_value" |
| M | Primary Key | String | Always | `Y` or `N` |
| N | Schema Name | String | Always | Target schema name |
| O | Database Name | String | Always | Target database name |
| P | References | String | Always for populated detail rows | Row-level evidence references separated by `; ` (for example `BRD-001; SRC-014; RULE-003`). Blank is invalid for populated rows. |
| Q | Comments | String | Optional | Additional notes. Blank if none. |

### Row Ordering (within each table sheet)

Rows must follow this order:
1. **Surrogate Key** (Role: surrogate_key, PK: Y) — if applicable
2. **Business Key columns** (Role: business_key, Nullable: N)
3. **Attribute columns** (Role: attribute) — in logical grouping order
4. **Audit columns** (Role: audit) — always last, always in this exact order:
   - INRT_DT | TIMESTAMP | N | audit | "System generated column"
   - INRT_BY | VARCHAR | N | audit | "System generated column"
   - CYCL_TIME_ID | VARCHAR | N | audit | "System generated column"
   - UPDT_DT | TIMESTAMP | N | audit | "System generated column"
   - UPDT_BY | VARCHAR | N | audit | "System generated column"

### Transformation Logic Rules (Column I)

| Scenario | Value |
|----------|-------|
| 1:1 direct from source | `Direct mapping.` (note the period) |
| Surrogate key (no source) | `Auto Generated column. New record: increment target value by 1 for each new record. If table is empty, start with 1.` |
| Audit columns | `System generated column` |
| Type cast | `Cast {source_type} to {target_type}. Direct mapping.` |
| Rename | `Direct mapping. Renamed from {source_column}.` |
| Lookup | `Lookup {key_column} in {dim_table} to get {sk_column}.` |
| Aggregation | `{FUNCTION}({column}) grouped by {columns}.` |
| Date conversion | `Convert {source_format} to {target_format}.` |
| Calculation | Full description quoting the business rule |
| Conditional | `CASE WHEN ... THEN ... ELSE ... END.` |

**NEVER use vague logic:** "Derived from source", "Transformed", "Business logic applied"

### Column Description Rules (Column L)

Format: `"{description}\nSample Data: {value}"`

- Description: Concise business meaning of the column
- Sample Data: One representative example value from source data or business rule
- For audit columns: Description = "Audit"
- For surrogate keys: Description = "Surrogate key uniquely identifying the {entity} record.\nSample Data: 1"


## CROSS-CONSISTENCY REQUIREMENT

Every column in the STTM Target Column (col B) must have a matching:
- Data Model Attribute Name (col F) — same name, same type, same role
- DQ Column Name (col E) — if a DQ check exists for that column


## TRACEABILITY / REFERENCES REQUIREMENT

Every populated detail row must have a non-empty `References` cell. Use `.claude/skills/design-agent/utilities/traceability-reference-policy.md` for allowed prefixes and evidence-registry rules. Multiple references are separated with `; `. Rows generated from `config/project_config.json` defaults, such as audit columns or standard DQ rules, still require references such as `CONFIG-audit-columns` or `PKG-dq-patterns-business-key`.
