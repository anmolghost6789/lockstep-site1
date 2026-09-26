-- ============================================================================
-- LEGACY PATTERNS — MULTI-DIALECT REFERENCE
-- ============================================================================
-- Place existing SQL examples here that show how current loads work in your
-- target dialect. The Build Agent uses these as implementation pattern
-- references — not as source code to copy. The agent will learn merge patterns,
-- join styles, DQ implementation approaches, and coding conventions from these
-- examples.
--
-- HOW THE AGENT MATCHES DIALECTS:
-- Each section below is tagged with a -- DIALECT: <name> marker. The agent
-- reads enterprise_context.md::SQL Dialect (and project_context.md overrides)
-- and selects the matching section. Sections that do not match the target
-- dialect are ignored.
--
-- Supported dialect tags:
--   DIALECT: snowflake
--   DIALECT: bigquery
--   DIALECT: synapse       (Azure Synapse / SQL Server T-SQL)
--   DIALECT: databricks    (Databricks Spark SQL / Delta Lake)
--   DIALECT: redshift
--
-- You can delete any section that does not apply to your project. You can also
-- add your own sections — use the same DIALECT: <name> marker convention so
-- the agent can route to them.
--
-- Include whatever you have: full stored procedures, partial scripts, code
-- snippets, or commented pseudocode. The agent extracts what is useful and
-- adapts it to the current build conventions.
-- ============================================================================


-- ############################################################################
-- DIALECT: snowflake
-- ############################################################################

-- ============================================================================
-- SNOWFLAKE — EXAMPLE 1: Full Load Pattern (Dimension)
-- ============================================================================

-- TRUNCATE TABLE edw_dw.d_product;
--
-- INSERT INTO edw_dw.d_product (
--     PRODUCT_SK, PRODUCT_ID, PRODUCT_NAME,
--     CATEGORY_L1, CATEGORY_L2, BRAND,
--     UNIT_PRICE, UNIT_COST, IS_ACTIVE,
--     INRT_DT, UPDT_DT
-- )
-- SELECT
--     ROW_NUMBER() OVER (ORDER BY s.product_id)         AS PRODUCT_SK,
--     s.product_id                                       AS PRODUCT_ID,
--     TRIM(s.product_name)                               AS PRODUCT_NAME,
--     TRIM(SPLIT_PART(s.category, '>', 1))               AS CATEGORY_L1,
--     NULLIF(TRIM(SPLIT_PART(s.category, '>', 2)), '')   AS CATEGORY_L2,
--     UPPER(s.brand)                                     AS BRAND,
--     s.list_price                                       AS UNIT_PRICE,
--     s.cost                                             AS UNIT_COST,
--     CASE WHEN s.status = 'ACTIVE' THEN TRUE ELSE FALSE END AS IS_ACTIVE,
--     CURRENT_TIMESTAMP                                  AS INRT_DT,
--     CURRENT_TIMESTAMP                                  AS UPDT_DT
-- FROM edw_staging.erp_product_master s;


-- ============================================================================
-- SNOWFLAKE — EXAMPLE 2: SCD2 Merge Pattern (Dimension)
-- ============================================================================

-- MERGE INTO edw_dw.d_customer AS tgt
-- USING (
--     SELECT
--         src.CUSTOMER_ID,
--         src.FIRST_NAME, src.LAST_NAME,
--         TRIM(src.FIRST_NAME) || ' ' || TRIM(src.LAST_NAME) AS FULL_NAME,
--         src.EMAIL, src.PHONE, src.CUSTOMER_SEGMENT,
--         src.CITY, src.STATE_PROVINCE, src.COUNTRY_CD, src.POSTAL_CODE,
--         MD5(COALESCE(src.EMAIL,'') || '|' ||
--             COALESCE(src.PHONE,'') || '|' ||
--             COALESCE(src.CUSTOMER_SEGMENT,'') || '|' ||
--             COALESCE(src.CITY,'') || '|' ||
--             COALESCE(src.STATE_PROVINCE,'') || '|' ||
--             COALESCE(src.COUNTRY_CD,'')) AS RECORD_HASH
--     FROM edw_staging.stg_customer_raw src
-- ) AS src
-- ON tgt.CUSTOMER_ID = src.CUSTOMER_ID
--    AND tgt.IS_CURRENT = TRUE
-- WHEN MATCHED AND tgt.RECORD_HASH <> src.RECORD_HASH THEN
--     UPDATE SET
--         tgt.EFF_END_DT = DATEADD(DAY, -1, CURRENT_DATE),
--         tgt.IS_CURRENT = FALSE,
--         tgt.UPDT_DT    = CURRENT_TIMESTAMP,
--         tgt.UPDT_BY    = CURRENT_USER
-- WHEN NOT MATCHED THEN
--     INSERT (CUSTOMER_ID, FIRST_NAME, LAST_NAME, FULL_NAME,
--             EMAIL, PHONE, CUSTOMER_SEGMENT, CITY, STATE_PROVINCE,
--             COUNTRY_CD, POSTAL_CODE,
--             EFF_START_DT, EFF_END_DT, IS_CURRENT, RECORD_HASH,
--             INRT_DT, INRT_BY, UPDT_DT, UPDT_BY)
--     VALUES (src.CUSTOMER_ID, src.FIRST_NAME, src.LAST_NAME, src.FULL_NAME,
--             src.EMAIL, src.PHONE, src.CUSTOMER_SEGMENT, src.CITY,
--             src.STATE_PROVINCE, src.COUNTRY_CD, src.POSTAL_CODE,
--             CURRENT_DATE, NULL, TRUE, src.RECORD_HASH,
--             CURRENT_TIMESTAMP, CURRENT_USER, CURRENT_TIMESTAMP, CURRENT_USER);
-- -- Note: after MERGE, run a second INSERT for new-version rows of changed records.


-- ============================================================================
-- SNOWFLAKE — EXAMPLE 3: Incremental Fact Load Pattern
-- ============================================================================

-- INSERT INTO edw_dw.f_sales (
--     ORDER_ID, ORDER_LINE_NUM, CUSTOMER_SK, PRODUCT_SK,
--     ORDER_DATE, QUANTITY, UNIT_PRICE, DISCOUNT_PCT,
--     LINE_TOTAL, TAX_AMOUNT, CHANNEL_CD, INRT_DT, UPDT_DT
-- )
-- SELECT
--     o.order_id, o.line_number,
--     COALESCE(dc.CUSTOMER_SK, -1) AS CUSTOMER_SK,
--     COALESCE(dp.PRODUCT_SK, -1)  AS PRODUCT_SK,
--     CAST(o.order_date AS DATE)   AS ORDER_DATE,
--     o.qty, o.unit_price,
--     COALESCE(o.discount, 0)      AS DISCOUNT_PCT,
--     ROUND(o.qty * o.unit_price * (1 - COALESCE(o.discount, 0) / 100), 2) AS LINE_TOTAL,
--     COALESCE(o.tax, 0)           AS TAX_AMOUNT,
--     o.channel                    AS CHANNEL_CD,
--     CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
-- FROM edw_staging.stg_orders o
-- LEFT JOIN edw_dw.d_customer dc
--     ON o.customer_id = dc.CUSTOMER_ID
--    AND dc.IS_CURRENT = TRUE
-- LEFT JOIN edw_dw.d_product dp
--     ON o.product_id = dp.PRODUCT_ID
-- WHERE o.order_date >= '{last_load_date}';


-- ============================================================================
-- SNOWFLAKE — EXAMPLE 4: DQ Check Pattern (procedural SQL)
-- ============================================================================

-- SELECT 'stg_customer_raw' AS table_name,
--        'CUSTOMER_ID'      AS column_name,
--        'Not Null'         AS check_type,
--        'C'                AS criticality,
--        COUNT(*)           AS total_rows,
--        SUM(CASE WHEN CUSTOMER_ID IS NULL THEN 1 ELSE 0 END) AS failed_rows,
--        ROUND(SUM(CASE WHEN CUSTOMER_ID IS NULL THEN 1 ELSE 0 END)
--              * 100.0 / NULLIF(COUNT(*), 0), 2) AS failure_pct
-- FROM edw_staging.stg_customer_raw;



-- ############################################################################
-- DIALECT: bigquery
-- ############################################################################

-- ============================================================================
-- BIGQUERY — EXAMPLE 1: Full Load Pattern (Dimension)
-- ============================================================================
-- Notes: BigQuery uses backticks for identifiers, Standard SQL only. Use
-- TRUNCATE TABLE for atomic full replace; INSERT SELECT otherwise.

-- TRUNCATE TABLE `project.edw_dw.d_product`;
--
-- INSERT INTO `project.edw_dw.d_product` (
--     PRODUCT_SK, PRODUCT_ID, PRODUCT_NAME,
--     CATEGORY_L1, CATEGORY_L2, BRAND,
--     UNIT_PRICE, UNIT_COST, IS_ACTIVE,
--     INRT_DT, UPDT_DT
-- )
-- SELECT
--     ROW_NUMBER() OVER (ORDER BY s.product_id)                        AS PRODUCT_SK,
--     s.product_id                                                      AS PRODUCT_ID,
--     TRIM(s.product_name)                                              AS PRODUCT_NAME,
--     TRIM(SPLIT(s.category, '>')[SAFE_OFFSET(0)])                      AS CATEGORY_L1,
--     NULLIF(TRIM(SPLIT(s.category, '>')[SAFE_OFFSET(1)]), '')          AS CATEGORY_L2,
--     UPPER(s.brand)                                                    AS BRAND,
--     s.list_price                                                      AS UNIT_PRICE,
--     s.cost                                                            AS UNIT_COST,
--     IF(s.status = 'ACTIVE', TRUE, FALSE)                              AS IS_ACTIVE,
--     CURRENT_TIMESTAMP()                                               AS INRT_DT,
--     CURRENT_TIMESTAMP()                                               AS UPDT_DT
-- FROM `project.edw_staging.erp_product_master` s;


-- ============================================================================
-- BIGQUERY — EXAMPLE 2: SCD2 Merge Pattern (Dimension)
-- ============================================================================
-- Notes: BigQuery MERGE supports a single DML statement with INSERT+UPDATE.
-- Use FARM_FINGERPRINT for deterministic hash OR TO_HEX(SHA256(...)) for
-- cryptographic hash. Prefer FARM_FINGERPRINT for performance.

-- MERGE INTO `project.edw_dw.d_customer` AS tgt
-- USING (
--     SELECT
--         src.CUSTOMER_ID,
--         src.FIRST_NAME, src.LAST_NAME,
--         CONCAT(TRIM(src.FIRST_NAME), ' ', TRIM(src.LAST_NAME)) AS FULL_NAME,
--         src.EMAIL, src.PHONE, src.CUSTOMER_SEGMENT,
--         src.CITY, src.STATE_PROVINCE, src.COUNTRY_CD, src.POSTAL_CODE,
--         FARM_FINGERPRINT(CONCAT(
--             IFNULL(src.EMAIL,''), '|',
--             IFNULL(src.PHONE,''), '|',
--             IFNULL(src.CUSTOMER_SEGMENT,''), '|',
--             IFNULL(src.CITY,''), '|',
--             IFNULL(src.STATE_PROVINCE,''), '|',
--             IFNULL(src.COUNTRY_CD,'')
--         )) AS RECORD_HASH
--     FROM `project.edw_staging.stg_customer_raw` src
-- ) AS src
-- ON tgt.CUSTOMER_ID = src.CUSTOMER_ID AND tgt.IS_CURRENT = TRUE
-- WHEN MATCHED AND tgt.RECORD_HASH <> src.RECORD_HASH THEN
--     UPDATE SET
--         EFF_END_DT = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY),
--         IS_CURRENT = FALSE,
--         UPDT_DT    = CURRENT_TIMESTAMP(),
--         UPDT_BY    = SESSION_USER()
-- WHEN NOT MATCHED THEN
--     INSERT (CUSTOMER_ID, FIRST_NAME, LAST_NAME, FULL_NAME,
--             EMAIL, PHONE, CUSTOMER_SEGMENT, CITY, STATE_PROVINCE,
--             COUNTRY_CD, POSTAL_CODE,
--             EFF_START_DT, EFF_END_DT, IS_CURRENT, RECORD_HASH,
--             INRT_DT, INRT_BY, UPDT_DT, UPDT_BY)
--     VALUES (src.CUSTOMER_ID, src.FIRST_NAME, src.LAST_NAME, src.FULL_NAME,
--             src.EMAIL, src.PHONE, src.CUSTOMER_SEGMENT, src.CITY,
--             src.STATE_PROVINCE, src.COUNTRY_CD, src.POSTAL_CODE,
--             CURRENT_DATE(), NULL, TRUE, src.RECORD_HASH,
--             CURRENT_TIMESTAMP(), SESSION_USER(), CURRENT_TIMESTAMP(), SESSION_USER());


-- ============================================================================
-- BIGQUERY — EXAMPLE 3: Incremental Fact Load Pattern
-- ============================================================================

-- INSERT INTO `project.edw_dw.f_sales` (
--     ORDER_ID, ORDER_LINE_NUM, CUSTOMER_SK, PRODUCT_SK,
--     ORDER_DATE, QUANTITY, UNIT_PRICE, DISCOUNT_PCT,
--     LINE_TOTAL, TAX_AMOUNT, CHANNEL_CD, INRT_DT, UPDT_DT
-- )
-- SELECT
--     o.order_id, o.line_number,
--     IFNULL(dc.CUSTOMER_SK, -1) AS CUSTOMER_SK,
--     IFNULL(dp.PRODUCT_SK, -1)  AS PRODUCT_SK,
--     CAST(o.order_date AS DATE) AS ORDER_DATE,
--     o.qty, o.unit_price,
--     IFNULL(o.discount, 0)      AS DISCOUNT_PCT,
--     ROUND(o.qty * o.unit_price * (1 - IFNULL(o.discount, 0) / 100), 2) AS LINE_TOTAL,
--     IFNULL(o.tax, 0)           AS TAX_AMOUNT,
--     o.channel                  AS CHANNEL_CD,
--     CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
-- FROM `project.edw_staging.stg_orders` o
-- LEFT JOIN `project.edw_dw.d_customer` dc
--     ON o.customer_id = dc.CUSTOMER_ID AND dc.IS_CURRENT = TRUE
-- LEFT JOIN `project.edw_dw.d_product` dp
--     ON o.product_id = dp.PRODUCT_ID
-- WHERE o.order_date >= DATE('{last_load_date}');


-- ============================================================================
-- BIGQUERY — EXAMPLE 4: DQ Check Pattern (procedural SQL)
-- ============================================================================

-- SELECT 'stg_customer_raw' AS table_name,
--        'CUSTOMER_ID'      AS column_name,
--        'Not Null'         AS check_type,
--        'C'                AS criticality,
--        COUNT(*)           AS total_rows,
--        COUNTIF(CUSTOMER_ID IS NULL) AS failed_rows,
--        ROUND(COUNTIF(CUSTOMER_ID IS NULL) * 100.0 / NULLIF(COUNT(*), 0), 2) AS failure_pct
-- FROM `project.edw_staging.stg_customer_raw`;



-- ############################################################################
-- DIALECT: synapse
-- ############################################################################
-- Notes: Azure Synapse dedicated SQL pool uses T-SQL. Synapse does NOT support
-- MERGE on dedicated pools (as of 2024 GA) — use CTAS + rename or
-- DELETE+INSERT. On Synapse serverless, MERGE is supported. Examples below
-- assume dedicated SQL pool and use DELETE+INSERT as the safe baseline.

-- ============================================================================
-- SYNAPSE — EXAMPLE 1: Full Load Pattern (Dimension, CTAS swap)
-- ============================================================================

-- -- CTAS into a staging copy, then swap with RENAME for atomic replace
-- CREATE TABLE edw_dw.d_product_new
-- WITH (DISTRIBUTION = REPLICATE, CLUSTERED COLUMNSTORE INDEX)
-- AS
-- SELECT
--     ROW_NUMBER() OVER (ORDER BY s.product_id) AS PRODUCT_SK,
--     s.product_id                              AS PRODUCT_ID,
--     LTRIM(RTRIM(s.product_name))              AS PRODUCT_NAME,
--     LTRIM(RTRIM(PARSENAME(REPLACE(s.category, '>', '.'), 2))) AS CATEGORY_L1,
--     NULLIF(LTRIM(RTRIM(PARSENAME(REPLACE(s.category, '>', '.'), 1))), '') AS CATEGORY_L2,
--     UPPER(s.brand)                            AS BRAND,
--     s.list_price                              AS UNIT_PRICE,
--     s.cost                                    AS UNIT_COST,
--     CASE WHEN s.status = 'ACTIVE' THEN 1 ELSE 0 END AS IS_ACTIVE,
--     SYSUTCDATETIME()                          AS INRT_DT,
--     SYSUTCDATETIME()                          AS UPDT_DT
-- FROM edw_staging.erp_product_master s;
--
-- RENAME OBJECT edw_dw.d_product     TO d_product_old;
-- RENAME OBJECT edw_dw.d_product_new TO d_product;
-- DROP TABLE edw_dw.d_product_old;


-- ============================================================================
-- SYNAPSE — EXAMPLE 2: SCD2 Pattern (DELETE+INSERT, dedicated pool)
-- ============================================================================
-- Notes: HASHBYTES('MD5', ...) returns VARBINARY; convert to VARCHAR with
-- CONVERT(VARCHAR(32), ..., 2) for hex string comparison.

-- -- Step 1: identify changed business keys
-- WITH changed_keys AS (
--     SELECT src.CUSTOMER_ID
--     FROM edw_staging.stg_customer_raw src
--     INNER JOIN edw_dw.d_customer tgt
--        ON tgt.CUSTOMER_ID = src.CUSTOMER_ID AND tgt.IS_CURRENT = 1
--     WHERE tgt.RECORD_HASH <> CONVERT(VARCHAR(32), HASHBYTES('MD5',
--         CONCAT(
--             ISNULL(src.EMAIL,''), '|', ISNULL(src.PHONE,''), '|',
--             ISNULL(src.CUSTOMER_SEGMENT,''), '|', ISNULL(src.CITY,''), '|',
--             ISNULL(src.STATE_PROVINCE,''), '|', ISNULL(src.COUNTRY_CD,'')
--         )), 2)
-- )
-- -- Step 2: expire prior current row
-- UPDATE tgt
-- SET    EFF_END_DT = DATEADD(DAY, -1, CAST(SYSUTCDATETIME() AS DATE)),
--        IS_CURRENT = 0,
--        UPDT_DT    = SYSUTCDATETIME(),
--        UPDT_BY    = SUSER_SNAME()
-- FROM   edw_dw.d_customer tgt
-- INNER JOIN changed_keys ck ON ck.CUSTOMER_ID = tgt.CUSTOMER_ID
-- WHERE  tgt.IS_CURRENT = 1;
--
-- -- Step 3: insert new version for changed records + new records
-- INSERT INTO edw_dw.d_customer (CUSTOMER_ID, FIRST_NAME, LAST_NAME, FULL_NAME, ...,
--         EFF_START_DT, EFF_END_DT, IS_CURRENT, RECORD_HASH, INRT_DT, INRT_BY, UPDT_DT, UPDT_BY)
-- SELECT src.CUSTOMER_ID, src.FIRST_NAME, src.LAST_NAME,
--        LTRIM(RTRIM(src.FIRST_NAME)) + ' ' + LTRIM(RTRIM(src.LAST_NAME)), ...,
--        CAST(SYSUTCDATETIME() AS DATE), NULL, 1,
--        CONVERT(VARCHAR(32), HASHBYTES('MD5', CONCAT(...)), 2),
--        SYSUTCDATETIME(), SUSER_SNAME(), SYSUTCDATETIME(), SUSER_SNAME()
-- FROM edw_staging.stg_customer_raw src
-- LEFT JOIN edw_dw.d_customer tgt
--     ON tgt.CUSTOMER_ID = src.CUSTOMER_ID AND tgt.IS_CURRENT = 1
-- WHERE tgt.CUSTOMER_ID IS NULL
--    OR src.CUSTOMER_ID IN (SELECT CUSTOMER_ID FROM changed_keys);


-- ============================================================================
-- SYNAPSE — EXAMPLE 3: Incremental Fact Load Pattern
-- ============================================================================

-- INSERT INTO edw_dw.f_sales (ORDER_ID, ORDER_LINE_NUM, CUSTOMER_SK, PRODUCT_SK,
--     ORDER_DATE, QUANTITY, UNIT_PRICE, DISCOUNT_PCT, LINE_TOTAL, TAX_AMOUNT,
--     CHANNEL_CD, INRT_DT, UPDT_DT)
-- SELECT
--     o.order_id, o.line_number,
--     ISNULL(dc.CUSTOMER_SK, -1) AS CUSTOMER_SK,
--     ISNULL(dp.PRODUCT_SK, -1)  AS PRODUCT_SK,
--     CAST(o.order_date AS DATE) AS ORDER_DATE,
--     o.qty, o.unit_price,
--     ISNULL(o.discount, 0)      AS DISCOUNT_PCT,
--     ROUND(o.qty * o.unit_price * (1 - ISNULL(o.discount, 0) / 100.0), 2) AS LINE_TOTAL,
--     ISNULL(o.tax, 0)           AS TAX_AMOUNT,
--     o.channel                  AS CHANNEL_CD,
--     SYSUTCDATETIME(), SYSUTCDATETIME()
-- FROM edw_staging.stg_orders o
-- LEFT JOIN edw_dw.d_customer dc
--     ON o.customer_id = dc.CUSTOMER_ID AND dc.IS_CURRENT = 1
-- LEFT JOIN edw_dw.d_product  dp
--     ON o.product_id = dp.PRODUCT_ID
-- WHERE o.order_date >= '{last_load_date}';


-- ============================================================================
-- SYNAPSE — EXAMPLE 4: DQ Check Pattern
-- ============================================================================

-- SELECT 'stg_customer_raw' AS table_name,
--        'CUSTOMER_ID'      AS column_name,
--        'Not Null'         AS check_type,
--        'C'                AS criticality,
--        COUNT(*)           AS total_rows,
--        SUM(CASE WHEN CUSTOMER_ID IS NULL THEN 1 ELSE 0 END) AS failed_rows,
--        CAST(SUM(CASE WHEN CUSTOMER_ID IS NULL THEN 1 ELSE 0 END) * 100.0
--             / NULLIF(COUNT(*), 0) AS DECIMAL(5,2))           AS failure_pct
-- FROM edw_staging.stg_customer_raw;



-- ############################################################################
-- DIALECT: databricks
-- ############################################################################
-- Notes: Databricks Spark SQL / Delta Lake. MERGE INTO is fully supported on
-- Delta tables. Use sha2(col, 256) for cryptographic hash or xxhash64(col) for
-- deterministic non-cryptographic hash.

-- ============================================================================
-- DATABRICKS — EXAMPLE 1: Full Load Pattern (Dimension, CREATE OR REPLACE)
-- ============================================================================

-- CREATE OR REPLACE TABLE edw_dw.d_product
-- USING DELTA AS
-- SELECT
--     ROW_NUMBER() OVER (ORDER BY s.product_id)               AS PRODUCT_SK,
--     s.product_id                                             AS PRODUCT_ID,
--     TRIM(s.product_name)                                     AS PRODUCT_NAME,
--     TRIM(SPLIT(s.category, '>')[0])                          AS CATEGORY_L1,
--     NULLIF(TRIM(ELEMENT_AT(SPLIT(s.category, '>'), 2)), '')  AS CATEGORY_L2,
--     UPPER(s.brand)                                           AS BRAND,
--     s.list_price                                             AS UNIT_PRICE,
--     s.cost                                                   AS UNIT_COST,
--     CASE WHEN s.status = 'ACTIVE' THEN TRUE ELSE FALSE END   AS IS_ACTIVE,
--     CURRENT_TIMESTAMP()                                      AS INRT_DT,
--     CURRENT_TIMESTAMP()                                      AS UPDT_DT
-- FROM edw_staging.erp_product_master s;


-- ============================================================================
-- DATABRICKS — EXAMPLE 2: SCD2 Merge Pattern (Delta Lake)
-- ============================================================================

-- MERGE INTO edw_dw.d_customer AS tgt
-- USING (
--     SELECT
--         src.CUSTOMER_ID,
--         src.FIRST_NAME, src.LAST_NAME,
--         CONCAT(TRIM(src.FIRST_NAME), ' ', TRIM(src.LAST_NAME)) AS FULL_NAME,
--         src.EMAIL, src.PHONE, src.CUSTOMER_SEGMENT,
--         src.CITY, src.STATE_PROVINCE, src.COUNTRY_CD, src.POSTAL_CODE,
--         sha2(CONCAT_WS('|',
--             COALESCE(src.EMAIL,''),
--             COALESCE(src.PHONE,''),
--             COALESCE(src.CUSTOMER_SEGMENT,''),
--             COALESCE(src.CITY,''),
--             COALESCE(src.STATE_PROVINCE,''),
--             COALESCE(src.COUNTRY_CD,'')
--         ), 256) AS RECORD_HASH
--     FROM edw_staging.stg_customer_raw src
-- ) AS src
-- ON tgt.CUSTOMER_ID = src.CUSTOMER_ID AND tgt.IS_CURRENT = TRUE
-- WHEN MATCHED AND tgt.RECORD_HASH <> src.RECORD_HASH THEN
--     UPDATE SET
--         tgt.EFF_END_DT = DATE_SUB(CURRENT_DATE(), 1),
--         tgt.IS_CURRENT = FALSE,
--         tgt.UPDT_DT    = CURRENT_TIMESTAMP(),
--         tgt.UPDT_BY    = CURRENT_USER()
-- WHEN NOT MATCHED THEN
--     INSERT (CUSTOMER_ID, FIRST_NAME, LAST_NAME, FULL_NAME,
--             EMAIL, PHONE, CUSTOMER_SEGMENT, CITY, STATE_PROVINCE,
--             COUNTRY_CD, POSTAL_CODE,
--             EFF_START_DT, EFF_END_DT, IS_CURRENT, RECORD_HASH,
--             INRT_DT, INRT_BY, UPDT_DT, UPDT_BY)
--     VALUES (src.CUSTOMER_ID, src.FIRST_NAME, src.LAST_NAME, src.FULL_NAME,
--             src.EMAIL, src.PHONE, src.CUSTOMER_SEGMENT, src.CITY,
--             src.STATE_PROVINCE, src.COUNTRY_CD, src.POSTAL_CODE,
--             CURRENT_DATE(), NULL, TRUE, src.RECORD_HASH,
--             CURRENT_TIMESTAMP(), CURRENT_USER(), CURRENT_TIMESTAMP(), CURRENT_USER());


-- ============================================================================
-- DATABRICKS — EXAMPLE 3: Incremental Fact Load Pattern
-- ============================================================================

-- INSERT INTO edw_dw.f_sales (ORDER_ID, ORDER_LINE_NUM, CUSTOMER_SK, PRODUCT_SK,
--     ORDER_DATE, QUANTITY, UNIT_PRICE, DISCOUNT_PCT, LINE_TOTAL, TAX_AMOUNT,
--     CHANNEL_CD, INRT_DT, UPDT_DT)
-- SELECT
--     o.order_id, o.line_number,
--     COALESCE(dc.CUSTOMER_SK, -1) AS CUSTOMER_SK,
--     COALESCE(dp.PRODUCT_SK, -1)  AS PRODUCT_SK,
--     CAST(o.order_date AS DATE)   AS ORDER_DATE,
--     o.qty, o.unit_price,
--     COALESCE(o.discount, 0)      AS DISCOUNT_PCT,
--     ROUND(o.qty * o.unit_price * (1 - COALESCE(o.discount, 0) / 100), 2) AS LINE_TOTAL,
--     COALESCE(o.tax, 0)           AS TAX_AMOUNT,
--     o.channel                    AS CHANNEL_CD,
--     CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
-- FROM edw_staging.stg_orders o
-- LEFT JOIN edw_dw.d_customer dc
--     ON o.customer_id = dc.CUSTOMER_ID AND dc.IS_CURRENT = TRUE
-- LEFT JOIN edw_dw.d_product dp
--     ON o.product_id = dp.PRODUCT_ID
-- WHERE o.order_date >= DATE'{last_load_date}';


-- ============================================================================
-- DATABRICKS — EXAMPLE 4: DQ Check Pattern
-- ============================================================================

-- SELECT 'stg_customer_raw' AS table_name,
--        'CUSTOMER_ID'      AS column_name,
--        'Not Null'         AS check_type,
--        'C'                AS criticality,
--        COUNT(*)           AS total_rows,
--        SUM(CASE WHEN CUSTOMER_ID IS NULL THEN 1 ELSE 0 END) AS failed_rows,
--        ROUND(SUM(CASE WHEN CUSTOMER_ID IS NULL THEN 1 ELSE 0 END)
--              * 100.0 / NULLIF(COUNT(*), 0), 2) AS failure_pct
-- FROM edw_staging.stg_customer_raw;



-- ############################################################################
-- DIALECT: redshift
-- ############################################################################
-- Notes: Redshift supports MERGE (modern, since 2023) and classic
-- DELETE+INSERT. Use FUNC_SHA1 for hashing or MD5. SPLIT_PART and DATEADD are
-- available. Identifiers are case-insensitive by default; use double-quoted
-- names to force case preservation.

-- ============================================================================
-- REDSHIFT — EXAMPLE 1: Full Load Pattern (Dimension)
-- ============================================================================

-- TRUNCATE TABLE edw_dw.d_product;
--
-- INSERT INTO edw_dw.d_product (
--     PRODUCT_SK, PRODUCT_ID, PRODUCT_NAME,
--     CATEGORY_L1, CATEGORY_L2, BRAND,
--     UNIT_PRICE, UNIT_COST, IS_ACTIVE,
--     INRT_DT, UPDT_DT
-- )
-- SELECT
--     ROW_NUMBER() OVER (ORDER BY s.product_id)          AS PRODUCT_SK,
--     s.product_id                                        AS PRODUCT_ID,
--     TRIM(s.product_name)                                AS PRODUCT_NAME,
--     TRIM(SPLIT_PART(s.category, '>', 1))                AS CATEGORY_L1,
--     NULLIF(TRIM(SPLIT_PART(s.category, '>', 2)), '')    AS CATEGORY_L2,
--     UPPER(s.brand)                                      AS BRAND,
--     s.list_price                                        AS UNIT_PRICE,
--     s.cost                                              AS UNIT_COST,
--     CASE WHEN s.status = 'ACTIVE' THEN TRUE ELSE FALSE END AS IS_ACTIVE,
--     SYSDATE                                             AS INRT_DT,
--     SYSDATE                                             AS UPDT_DT
-- FROM edw_staging.erp_product_master s;


-- ============================================================================
-- REDSHIFT — EXAMPLE 2: SCD2 Pattern (MERGE, modern syntax)
-- ============================================================================

-- MERGE INTO edw_dw.d_customer
-- USING (
--     SELECT
--         src.CUSTOMER_ID,
--         src.FIRST_NAME, src.LAST_NAME,
--         TRIM(src.FIRST_NAME) || ' ' || TRIM(src.LAST_NAME) AS FULL_NAME,
--         src.EMAIL, src.PHONE, src.CUSTOMER_SEGMENT,
--         src.CITY, src.STATE_PROVINCE, src.COUNTRY_CD, src.POSTAL_CODE,
--         FUNC_SHA1(COALESCE(src.EMAIL,'') || '|' ||
--                   COALESCE(src.PHONE,'') || '|' ||
--                   COALESCE(src.CUSTOMER_SEGMENT,'') || '|' ||
--                   COALESCE(src.CITY,'') || '|' ||
--                   COALESCE(src.STATE_PROVINCE,'') || '|' ||
--                   COALESCE(src.COUNTRY_CD,'')) AS RECORD_HASH
--     FROM edw_staging.stg_customer_raw src
-- ) src
-- ON d_customer.CUSTOMER_ID = src.CUSTOMER_ID AND d_customer.IS_CURRENT = TRUE
-- WHEN MATCHED AND d_customer.RECORD_HASH <> src.RECORD_HASH THEN
--     UPDATE SET
--         EFF_END_DT = DATEADD(DAY, -1, CURRENT_DATE),
--         IS_CURRENT = FALSE,
--         UPDT_DT    = SYSDATE,
--         UPDT_BY    = CURRENT_USER
-- WHEN NOT MATCHED THEN
--     INSERT (CUSTOMER_ID, FIRST_NAME, LAST_NAME, FULL_NAME,
--             EMAIL, PHONE, CUSTOMER_SEGMENT, CITY, STATE_PROVINCE,
--             COUNTRY_CD, POSTAL_CODE,
--             EFF_START_DT, EFF_END_DT, IS_CURRENT, RECORD_HASH,
--             INRT_DT, INRT_BY, UPDT_DT, UPDT_BY)
--     VALUES (src.CUSTOMER_ID, src.FIRST_NAME, src.LAST_NAME, src.FULL_NAME,
--             src.EMAIL, src.PHONE, src.CUSTOMER_SEGMENT, src.CITY,
--             src.STATE_PROVINCE, src.COUNTRY_CD, src.POSTAL_CODE,
--             CURRENT_DATE, NULL, TRUE, src.RECORD_HASH,
--             SYSDATE, CURRENT_USER, SYSDATE, CURRENT_USER);


-- ============================================================================
-- REDSHIFT — EXAMPLE 3: Incremental Fact Load Pattern
-- ============================================================================

-- INSERT INTO edw_dw.f_sales (ORDER_ID, ORDER_LINE_NUM, CUSTOMER_SK, PRODUCT_SK,
--     ORDER_DATE, QUANTITY, UNIT_PRICE, DISCOUNT_PCT, LINE_TOTAL, TAX_AMOUNT,
--     CHANNEL_CD, INRT_DT, UPDT_DT)
-- SELECT
--     o.order_id, o.line_number,
--     NVL(dc.CUSTOMER_SK, -1) AS CUSTOMER_SK,
--     NVL(dp.PRODUCT_SK, -1)  AS PRODUCT_SK,
--     CAST(o.order_date AS DATE) AS ORDER_DATE,
--     o.qty, o.unit_price,
--     NVL(o.discount, 0)      AS DISCOUNT_PCT,
--     ROUND(o.qty * o.unit_price * (1 - NVL(o.discount, 0) / 100.0), 2) AS LINE_TOTAL,
--     NVL(o.tax, 0)           AS TAX_AMOUNT,
--     o.channel               AS CHANNEL_CD,
--     SYSDATE, SYSDATE
-- FROM edw_staging.stg_orders o
-- LEFT JOIN edw_dw.d_customer dc
--     ON o.customer_id = dc.CUSTOMER_ID AND dc.IS_CURRENT = TRUE
-- LEFT JOIN edw_dw.d_product  dp
--     ON o.product_id = dp.PRODUCT_ID
-- WHERE o.order_date >= '{last_load_date}';


-- ============================================================================
-- REDSHIFT — EXAMPLE 4: DQ Check Pattern
-- ============================================================================

-- SELECT 'stg_customer_raw' AS table_name,
--        'CUSTOMER_ID'      AS column_name,
--        'Not Null'         AS check_type,
--        'C'                AS criticality,
--        COUNT(*)           AS total_rows,
--        SUM(CASE WHEN CUSTOMER_ID IS NULL THEN 1 ELSE 0 END) AS failed_rows,
--        ROUND(SUM(CASE WHEN CUSTOMER_ID IS NULL THEN 1 ELSE 0 END)
--              * 100.0 / NULLIF(COUNT(*), 0), 2) AS failure_pct
-- FROM edw_staging.stg_customer_raw;


-- ============================================================================
-- ADD YOUR LEGACY SQL BELOW
-- ============================================================================
-- Paste or write your actual legacy load scripts, merge patterns, DQ checks,
-- or any reference SQL that shows how current processes work. Prefix each
-- section with the matching DIALECT: <name> marker so the agent can route
-- correctly.
