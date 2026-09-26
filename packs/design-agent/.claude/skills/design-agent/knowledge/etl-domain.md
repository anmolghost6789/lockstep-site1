
# ETL DOMAIN KNOWLEDGE

## CORE CONCEPTS

### Dimensional Modeling
- **Dimension Tables**: Descriptive entities (who, what, where, when). Typically prefixed `d_` or `dim_`. Contain surrogate keys, business keys, and descriptive attributes. Usually smaller in row count. Loading strategy: Full/Truncate load.
- **Fact Tables**: Measurable events/transactions. Typically prefixed `f_` or `fct_`. Contain foreign keys to dimensions (surrogate keys) and measure columns (quantities, amounts, counts). Usually largest tables. Loading strategy: Incremental or Full.
- **Reference Tables**: Lookup/classification tables. Prefixed `ref_`. Small, relatively static.
- **Cross-Reference Tables**: Bridge or mapping tables. Prefixed `xref_`. Map many-to-many relationships.

### Surrogate Keys
- Auto-generated integer or VARCHAR identifiers that replace natural/business keys as the primary key in dimension tables.
- Purpose: Insulate the data warehouse from source system key changes.
- Convention: `{TABLE_SHORT_NAME}_SK` (e.g., `ATC_SK`, `CMPNY_SK`)
- Generation logic: Auto-increment, starting from 1.
- Always VARCHAR type (unless client convention specifies INTEGER).
- Always NOT NULL, always PRIMARY KEY.

### Business Keys
- Natural keys from the source system that uniquely identify a record in business terms.
- Examples: CMPNY_CD (Company Code), PACK_CD (Pack Code), ENT_CUST_ID (Enterprise Customer ID)
- NOT NULL, but NOT the primary key in dimensional model (SK is the PK).
- Used for matching/lookup during SK generation.

### Audit Columns
- System-generated metadata columns tracking when and by whom records were inserted/updated.
- Standard set: INRT_DT, INRT_BY, CYCL_TIME_ID, UPDT_DT, UPDT_BY
- Always present on every table. Always NOT NULL. Always at the end of the column list.
- Transformation logic: "System generated column"

### Loading Strategies
- **Full Load**: Truncate target and reload all records from source. Used for small dimension tables.
- **Incremental Load**: Insert new records, update changed records. Used for large fact tables.
- **Truncate Load**: Same as Full Load — truncate and reload. Common terminology variation.
- **SCD Type 1**: Overwrite old values with new values (no history). Most common for dimensions.
- **SCD Type 2**: Keep history by creating new records for changes (rare, complex).

### Data Types (Common)
- VARCHAR / VARCHAR(n): Variable-length text
- INTEGER / INT: Whole numbers
- FLOAT / DOUBLE: Decimal numbers
- NUMBER(p,s): Fixed-precision decimal (precision p, scale s)
- TIMESTAMP: Date and time
- DATE: Date only
- BOOLEAN: True/False

## LAYERED ARCHITECTURE PATTERNS

### Medallion Architecture (Bronze/Silver/Gold)
Similar to L0/L1/L2+:
- Bronze (L0): Raw, as-is from source
- Silver (L1): Cleansed, standardized, typed
- Gold (L2+): Business-ready, modeled, aggregated

### Raw → Staging → DW → Mart
- Raw (L0): 1:1 source mirror
- Staging (L1): Cleansed, deduped, type-cast
- Data Warehouse (L2): Dimensional model (dims + facts)
- Data Mart (L3+): Subject-specific aggregations

### Key Principle: Each Layer Adds Value
- L0: Makes data available in the warehouse platform
- L1: Makes data clean and consistent
- L2: Makes data business-meaningful (dimensional model)
- L3+: Makes data analytics-ready (aggregations, KPIs)

## DATA QUALITY PRINCIPLES

- **Completeness**: No missing values where values are expected
- **Validity**: Values conform to expected formats and ranges
- **Consistency**: Values agree across related tables
- **Timeliness**: Data is current and loaded on schedule
- **Uniqueness**: No duplicate records where uniqueness is expected
- **Referential Integrity**: Foreign keys point to existing primary keys
