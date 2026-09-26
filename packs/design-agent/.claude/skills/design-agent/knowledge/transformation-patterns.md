
# TRANSFORMATION PATTERNS

## PATTERN CATALOG

### 1. Direct Mapping
**When:** Source column maps 1:1 to target column with no changes.
**Logic:** `Direct mapping.`
**Source/Target:** Source table and column populated. Data types match.

### 2. Direct Mapping with Rename
**When:** Column is renamed but value is unchanged.
**Logic:** `Direct mapping. Renamed from {source_column}.`

### 3. Type Cast
**When:** Data type changes but value is semantically the same.
**Logic:** `Cast {source_type} to {target_type}. Direct mapping.`
**Example:** `Cast NUMBER(38,0) to VARCHAR. Direct mapping.`

### 4. Surrogate Key Generation
**When:** Auto-generated unique identifier for dimension records.
**Logic:** `Auto Generated column. New record: increment target value by 1 for each new record. If table is empty, start with 1.`
**Source:** `-` for both table and column.

### 5. System Generated (Audit)
**When:** Audit/metadata columns populated by the system at load time.
**Logic:** `System generated column`
**Source:** `-` for both table and column.

### 6. Lookup / Foreign Key Resolution
**When:** A business key in the source is replaced with a surrogate key from a dimension table.
**Logic:** `Lookup {business_key} in {dimension_table} to get {surrogate_key}.`
**Example:** `Lookup CMPNY_CD in d_cmpny to get CMPNY_SK.`
**Join Condition (col K):** `source.CMPNY_CD = d_cmpny.CMPNY_CD`

### 7. Multi-Column Lookup
**When:** The lookup key is a composite of multiple columns.
**Logic:** `Lookup ({col1}, {col2}, {col3}) in {dim_table} to get {sk}.`
**Example:** `Lookup (ATC1, ATC2, ATC3, ATC4) in d_atc to get ATC_SK.`
**Join Condition:** `source.ATC1 = d_atc.ATC1 AND source.ATC2 = d_atc.ATC2 AND source.ATC3 = d_atc.ATC3 AND source.ATC4 = d_atc.ATC4`

### 8. Aggregation
**When:** Values are aggregated from detail to summary level.
**Logic:** `{FUNCTION}({column}) grouped by {grouping_columns}.`
**Example:** `SUM(SALES_AMT) grouped by CMPNY_CD, PACK_CD, YM.`
**Common functions:** SUM, COUNT, AVG, MIN, MAX, COUNT DISTINCT

### 9. Date/Time Conversion
**When:** Date values need format changes.
**Logic:** `Convert {source_format} to {target_format}.`
**Example:** `Convert YYYYMM string to DATE (last day of month).`

### 10. String Transformation
**When:** String values are modified.
**Logic:** Specific description.
**Examples:**
- `UPPER({column})` — Convert to uppercase
- `TRIM({column})` — Remove leading/trailing whitespace
- `CONCAT({col1}, ' ', {col2})` — Concatenate columns
- `SUBSTR({column}, 1, 4)` — Extract substring

### 11. Conditional / CASE Logic
**When:** Value depends on a condition.
**Logic:** `CASE WHEN {condition} THEN {value1} WHEN {condition2} THEN {value2} ELSE {default} END.`
**Example:** `CASE WHEN ACTIVE_STATUS = 'Y' THEN 'Active' ELSE 'Inactive' END.`

### 12. Filtered Mapping
**When:** Only certain rows from source are included.
**Logic:** `Direct mapping.` (in Transformation Logic column)
**Filter Condition (col J):** `WHERE {condition}`
**Example:** Filter Condition: `WHERE COUNTRY_CD = 'US' AND ACTIVE_FLG = 'Y'`

### 13. Join-Based Enrichment
**When:** Target column comes from a different table than the primary source via a JOIN.
**Logic:** `Joined from {secondary_table}.{column} via {join_key}.`
**Join Condition (col K):** `LEFT JOIN {secondary_table} ON source.{key} = {secondary_table}.{key}`

### 14. Deduplication
**When:** Duplicate records are removed.
**Logic:** `DISTINCT on ({columns}).` or `ROW_NUMBER() OVER (PARTITION BY {key} ORDER BY {sort}) = 1.`

### 15. Default Value Assignment
**When:** NULL values are replaced with defaults.
**Logic:** `COALESCE({column}, {default_value}).`
**Example:** `COALESCE(BRAND_NM, 'Unknown').`

### 16. Rank / Window Function
**When:** Position/rank is calculated.
**Logic:** `ROW_NUMBER() OVER (PARTITION BY {partition_cols} ORDER BY {order_cols} {direction}).`


## RULES FOR WRITING TRANSFORMATION LOGIC

1. **Be specific.** Name exact columns, tables, and functions.
2. **Reference source from the correct layer.** L2 transformations reference L1 tables (not original sources).
3. **Use actual column names.** Not "the code column" but "CMPNY_CD".
4. **Include all parts.** If a transformation involves a filter AND a join AND an aggregation, describe all three.
5. **Match business rule language** where possible. If the BRD says "Only active brands are included," write the filter condition using similar phrasing.
6. **Never use placeholders** like "TBD", "To be defined", or "Business logic" in the Transformation Logic column. If the logic is unknown, stop and ask the human.
