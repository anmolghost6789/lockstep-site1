# Business Rules

> Document business rules that affect how data should be transformed, validated, and interpreted. These rules supplement what is already captured in the STTM's Transformation Logic column — use this file for rules that are too complex, cross-table, or context-dependent to fit in a single spreadsheet cell.

## Derivation Rules

> Rules for how derived or calculated fields should be computed.

### [Rule Name, e.g., Net Revenue Calculation]

- **Applies to:** [e.g., f_sales.LINE_TOTAL]
- **Formula:** [e.g., QUANTITY * UNIT_PRICE * (1 - COALESCE(DISCOUNT_PCT, 0) / 100)]
- **Rounding:** [e.g., Round to 2 decimal places]
- **Edge cases:** [e.g., If QUANTITY is NULL or <= 0, set LINE_TOTAL to 0 and flag for DQ]
- **Notes:** [e.g., Tax is excluded from LINE_TOTAL — it is stored separately]

### [Rule Name]

- **Applies to:**
- **Formula:**
- **Edge cases:**
- **Notes:**

## SCD2 Behavior Rules

> Detailed rules for how slowly changing dimensions should behave.

### [Dimension Name, e.g., d_customer]

- **Business Key:** [e.g., CUSTOMER_ID]
- **Tracked Columns:** [e.g., EMAIL, PHONE, CUSTOMER_SEGMENT, CITY, STATE_PROVINCE, COUNTRY_CD]
- **Non-Tracked Columns:** [e.g., POSTAL_CODE — changes are overwritten (SCD1)]
- **Change Detection Method:** [e.g., MD5 hash of tracked columns]
- **Version Start Logic:** [e.g., EFF_START_DT = CURRENT_DATE for new version]
- **Version End Logic:** [e.g., EFF_END_DT = new version start date minus 1 day]
- **Current Flag:** [e.g., IS_CURRENT = TRUE for latest version, FALSE for all prior]
- **Late-Arriving Dimension:** [e.g., If a fact references a customer not yet in the dimension, insert an inferred member with IS_CURRENT = TRUE and flag confidence as low]

## Lookup and Reference Rules

> Rules for how dimension lookups should behave in fact table loads.

### Unknown Member Handling

- **Default SK for missing lookups:** [e.g., -1]
- **Unknown member row required:** [e.g., Yes — every dimension must have a row with SK = -1, business key = 'UNKNOWN']
- **Behavior on lookup miss:** [e.g., Use -1 and log a DQ warning, do not reject the fact row]

### Multi-Version Lookup (SCD2 Dimensions)

- [e.g., Fact table should always join to the current version: WHERE IS_CURRENT = TRUE]
- [e.g., For point-in-time reporting, join on ORDER_DATE BETWEEN EFF_START_DT AND COALESCE(EFF_END_DT, '9999-12-31')]

## Precedence Rules

> When multiple sources or rules conflict, which one wins?

- [e.g., If CRM and ERP disagree on customer name, CRM takes precedence]
- [e.g., If STTM transformation logic conflicts with a business rule in this file, this file takes precedence]
- [e.g., User instructions override everything except data integrity constraints]

## Exception Handling

> How should the agent handle known exceptional situations?

### [Exception Name, e.g., Legacy Customer IDs]

- **Description:** [e.g., Customers loaded before 2020 use a 6-digit ID format. Post-2020 customers use UUID format.]
- **Handling:** [e.g., Normalize both to VARCHAR. Do not cast to INT.]
- **Affected Tables:** [e.g., stg_customer_raw, d_customer]

### [Exception Name]

- **Description:**
- **Handling:**
- **Affected Tables:**

## Filter and Inclusion Rules

> Rules about what data should be included or excluded from loads.

- [e.g., Exclude test orders where ORDER_ID starts with 'TEST_']
- [e.g., Only include active products (status = 'ACTIVE') in the product dimension]
- [e.g., For incremental loads, always use >= on the watermark date, not >]

## Aggregation Rules

> If any tables involve pre-aggregation, document the grain and aggregation logic.

- [e.g., f_sales_daily: aggregate f_sales to one row per CUSTOMER_SK + PRODUCT_SK + ORDER_DATE, summing QUANTITY, LINE_TOTAL, TAX_AMOUNT]

## Cross-Table Business Rules

> Rules that span multiple tables and cannot be captured in a single STTM row.

- [e.g., After loading d_customer, verify that every CUSTOMER_SK referenced in f_sales exists in d_customer]
- [e.g., Product pricing in f_sales should not exceed d_product.UNIT_PRICE by more than 20% — flag as DQ warning if it does]
