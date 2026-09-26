
# DATA MODEL TEMPLATE SPECIFICATION

## WORKBOOK STRUCTURE

Each Data Model workbook is **per layer** and contains:
- Sheet 1: `table_tracker` (index of all tables)
- Sheet 2+: One sheet per target table (sheet name = table name in lowercase)


## SHEET: table_tracker

| Column | Header | Content |
|--------|--------|---------|
| A | S. No. | Sequential integer starting at 1 |
| B | Table Name | Target table name (lowercase, matches sheet name) |
| C | Comments | Optional notes |


## TABLE SHEETS: Summary Section (Rows 1-7)

| Row | Cols A-B (merged) | Col C onward (merged to N) |
|-----|-------------------|---------------------------|
| 1 | DATA MODEL - SUMMARY | (merged A1:N1) |
| 2 | Layer: | Layer identifier |
| 3 | Table Description: | Full description |
| 4 | Loading Strategy | Strategy name |
| 5 | Schema Name | Target schema |
| 6 | Database Name | Target database |
| 7 | Frequency | Refresh frequency |

**Merged Cells:**
- A1:N1 (header)
- A{n}:B{n} for rows 2-7 (labels)
- C{n}:N{n} for rows 2-7 (values)


## TABLE SHEETS: Detail Section

| Row | Content |
|-----|---------|
| 8 | "DATA MODEL - DETAILS" (merged A8:N8) |
| 9 | Column headers (14 columns, A through N) |
| 10+ | Data rows — one per column in the table |

### Detail Column Definitions (14 columns)

| Col | Header | Required | Description |
|-----|--------|----------|-------------|
| A | S.No. | Always | Sequential ordinal (1, 2, 3...) |
| B | Schema Name | Always | Target schema name |
| C | Database Name | Always | Target database name |
| D | Table Name | Always | Target table name |
| E | Logical Name | Always | Human-readable column name (see rules below) |
| F | Attribute Name | Always | Technical column name (UPPER_SNAKE_CASE) |
| G | Data Type | Always | Target data type |
| H | Role | Always | `surrogate_key`, `business_key`, `attribute`, `audit` |
| I | Nullable | Always | `Y` or `N` |
| J | Primary Key | Always | `Y` or `N` |
| K | Column Description | Always | Description with sample data |
| L | Ordinal Position | Always | Sequential position matching S.No. |
| M | References | Always for populated detail rows | Row-level evidence references separated by `; `; must align with STTM references for the same target column. |
| N | Comments | Optional | Additional notes |

### Logical Name Rules (Column E)

The Logical Name is a human-readable, business-friendly name for the column:
- Derived from column description where available
- For abbreviation-heavy names: expand to full words (e.g., "CMPNY_CD" → "Company Code")
- For surrogate keys: "{Entity} Surrogate Key" (e.g., "ATC Surrogate Key")
- For audit columns: "Insert Date", "Insert By", "Cycle Time ID", "Update Date", "Update By"
- General pattern: Title Case with spaces, no abbreviations unless standard industry terms
- Examples:
  - ATC1 → "ATC Level 1"
  - PACK_CD → "Pack Code"
  - DSTR_NM → "Distributor Name"
  - PAT_DY → "Patient Day"
  - ENT_CUST_ID → "Enterprise Customer ID"

### Row Ordering

Same as STTM: surrogate_key → business_key → attribute → audit

### Column Description (Column K)

Same format as STTM: `"Description\nSample Data: value"`

For audit columns: `"Audit"`


## CONSISTENCY WITH STTM

For every row in the Data Model, there MUST be a corresponding row in the STTM for the same table where:
- Data Model `Attribute Name` (F) = STTM `Target Column` (B)
- Data Model `Data Type` (G) = STTM `Target Data Type` (D)
- Data Model `Role` (H) = STTM `Role` (C)
- Data Model `Nullable` (I) = STTM `Target Nullable` (E)
- Data Model `Primary Key` (J) = STTM `Primary Key` (M)
- Data Model `Column Description` (K) = STTM `Column Description` (L)
- Data Model `References` (M) = STTM `References` (P)

If any mismatch exists, it is a consistency error that must be fixed.


## TRACEABILITY / REFERENCES REQUIREMENT

Every populated detail row must have a non-empty `References` cell. Use `.claude/skills/design-agent/utilities/traceability-reference-policy.md` for allowed prefixes and evidence-registry rules. Multiple references are separated with `; `. Rows generated from `config/project_config.json` defaults, such as audit columns or standard DQ rules, still require references such as `CONFIG-audit-columns` or `PKG-dq-patterns-business-key`.
