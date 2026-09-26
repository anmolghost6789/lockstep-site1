
# DQ PATTERNS CATALOG

## STANDARD DQ CHECKS

### Not NULL / Not Null
**Purpose:** Ensure a column has no null values.
**When to apply:**
- Business key columns (always, Criticality: C, Threshold: 10)
- Required attribute columns per business rules (C, 10)
- Audit columns (NC, 5)
**DQ Rule Expression:** `SELECT COUNT(*) FROM {table} WHERE {column} IS NULL`
**Note:** Template uses "Not NULL" (capitalized) for critical checks and "Not Null" for non-critical. Follow the existing convention.

### Uniqueness
**Purpose:** Ensure no duplicate values exist in a column (or combination of columns).
**When to apply:**
- Surrogate key columns (always, C, Threshold: 0)
- Primary key columns (always, C, 0)
- Natural/business key columns if they should be unique (C, 0)
**DQ Rule Expression:** `SELECT {column}, COUNT(*) FROM {table} GROUP BY {column} HAVING COUNT(*) > 1`

### Referential Integrity
**Purpose:** Ensure foreign key values exist in the referenced parent table.
**When to apply:**
- FK columns in fact tables that reference dimension SKs (C, 5)
- Any column that looks up a value from another table (C, 5)
**DQ Rule Expression:** `SELECT COUNT(*) FROM {child_table} c LEFT JOIN {parent_table} p ON c.{fk_column} = p.{pk_column} WHERE p.{pk_column} IS NULL`

### Date Format Check
**Purpose:** Ensure date/timestamp values conform to expected format.
**When to apply:**
- All DATE columns (NC, 10)
- All TIMESTAMP columns (NC, 10)
- Audit date columns: INRT_DT, UPDT_DT (NC, 10)
**DQ Rule Expression:** `SELECT COUNT(*) FROM {table} WHERE TRY_TO_DATE({column}) IS NULL AND {column} IS NOT NULL`

### Year month check
**Purpose:** Ensure year-month values are in YYYYMM format and represent valid dates.
**When to apply:**
- Columns storing year-month values (YM, YEAR_MONTH, etc.) (C, 10)
**DQ Rule Expression:** `SELECT COUNT(*) FROM {table} WHERE NOT REGEXP_LIKE({column}, '^[0-9]{6}$') OR CAST(SUBSTR({column},5,2) AS INT) NOT BETWEEN 1 AND 12`

### Range Check
**Purpose:** Ensure numeric values fall within expected bounds.
**When to apply:**
- Numeric columns with known valid ranges per business rules (NC, 15)
- Percentage columns (0-100)
- Quantity columns (>= 0)
**DQ Rule Expression:** `SELECT COUNT(*) FROM {table} WHERE {column} NOT BETWEEN {min} AND {max}`

### Pattern Check
**Purpose:** Ensure values match an expected format pattern.
**When to apply:**
- Code columns with known patterns (NC, 10)
- ID columns with specific formats
**DQ Rule Expression:** `SELECT COUNT(*) FROM {table} WHERE NOT REGEXP_LIKE({column}, '{pattern}')`

### Duplicate Check
**Purpose:** Ensure no duplicate records exist based on a composite key.
**When to apply:**
- Table-level check on composite business keys (C, 0)
**DQ Rule Expression:** `SELECT {key_columns}, COUNT(*) FROM {table} GROUP BY {key_columns} HAVING COUNT(*) > 1`

### Completeness Check
**Purpose:** Ensure a column is populated for a minimum percentage of records.
**When to apply:**
- Columns expected to be mostly populated but where some nulls are tolerable (NC, 20)
**DQ Rule Expression:** `SELECT (COUNT(*) - COUNT({column})) * 100.0 / COUNT(*) AS null_pct FROM {table}`

### Consistency Check
**Purpose:** Ensure values in one table are consistent with values in a related table.
**When to apply:**
- Cross-table value consistency checks (C, 5)
**DQ Rule Expression:** Custom per relationship


## AUTOMATIC DQ RULE ASSIGNMENT

When designing DQ rules in 04 - Design and materializing them in 06 - Execute, automatically assign checks based on column properties:

```python
def get_dq_checks(column):
    checks = []
    
    # Surrogate keys
    if column.role == "surrogate_key":
        checks.append({"check": "Uniqueness", "criticality": "C", "threshold": 0})
    
    # Business keys
    if column.role == "business_key":
        checks.append({"check": "Not NULL", "criticality": "C", "threshold": 10})
    
    # Audit columns
    if column.role == "audit":
        checks.append({"check": "Not Null", "criticality": "NC", "threshold": 5})
        if column.data_type in ("TIMESTAMP", "DATE"):
            checks.append({"check": "Date Format Check", "criticality": "NC", "threshold": 10})
    
    # Date/Timestamp attributes
    if column.role == "attribute" and column.data_type in ("TIMESTAMP", "DATE"):
        checks.append({"check": "Date Format Check", "criticality": "NC", "threshold": 10})
    
    # Year-month columns
    if column.role == "attribute" and is_year_month_column(column.name):
        checks.append({"check": "Not NULL", "criticality": "C", "threshold": 5})
        checks.append({"check": "Year month check", "criticality": "C", "threshold": 10})
    
    # FK columns (in fact tables)
    if column.is_foreign_key:
        checks.append({"check": "Referential Integrity", "criticality": "C", "threshold": 5})
    
    # Non-nullable attributes
    if column.nullable == "N" and column.role == "attribute":
        checks.append({"check": "Not NULL", "criticality": "C", "threshold": 10})
    
    return checks

def is_year_month_column(name):
    return name.upper() in ("YM", "YEAR_MONTH", "YR_MTH", "YYYYMM") or "YEAR_MONTH" in name.upper()
```
