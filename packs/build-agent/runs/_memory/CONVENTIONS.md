# Conventions

> Durable conventions established across runs. Each entry should include where it came from and whether it is still active.

<!-- Example entry format:

## [Convention ID]: [Short Title]

- **Status:** active | superseded | retired
- **Category:** naming | coding_style | platform | dq | delivery | audit
- **Convention:** [What the convention is]
- **Source:** [Where it came from — user instruction, context doc, inferred from pattern]
- **Established:** [Run ID or date]
- **Superseded by:** [Convention ID, if applicable]
- **Notes:** [Any additional context]

-->

## CONV-001: SQL naming and style (run_id_002)

- **Status:** active
- **Category:** naming / coding_style
- **Convention:** Identifiers lower_snake_case; SQL keywords UPPERCASE; 4-space indent; CTEs over subqueries; every artifact has comment header (target table, run_id, STTM ref, timestamp)
- **Source:** user_instructions.docx + legacy_patterns.sql
- **Established:** run_id_002 / 2026-05-19

## CONV-002: Schema and database layout

- **Status:** active
- **Category:** platform
- **Convention:** helixor_rw (L0), helixor_wk (L1), helixor_dw (L2); database = helixor_db_${env}
- **Source:** enterprise_context.docx + STTM table_tracker sheets
- **Established:** run_id_002 / 2026-05-19

## CONV-003: Audit columns (5-column set)

- **Status:** active
- **Category:** audit
- **Convention:** Every INSERT and MERGE populates INRT_DT TIMESTAMP, INRT_BY VARCHAR, CYCL_TIME_ID VARCHAR, UPDT_DT TIMESTAMP, UPDT_BY VARCHAR
- **Source:** user_instructions.docx + all STTM files (audit role columns)
- **Established:** run_id_002 / 2026-05-19

## CONV-004: Surrogate key pattern

- **Status:** active
- **Category:** coding_style
- **Convention:** ROW_NUMBER() OVER (ORDER BY business_key) + COALESCE(MAX(existing_sk), 0); VARCHAR prefix + zero-padding (e.g., HCP_000000000123). No sequences (Databricks does not support them natively).
- **Source:** user_instructions.docx + databricks_patterns_reference.docx
- **Established:** run_id_002 / 2026-05-19

## CONV-005: SCD2 two-step MERGE pattern

- **Status:** active
- **Category:** scd2
- **Convention:** Step 1: MERGE closes current versions (is_current='N', eff_end_dt=DATE_SUB(CURRENT_DATE(),1)) for changed BKs. Step 2: INSERT new versions (is_current='Y', eff_end_dt=NULL). Change detection via MD5(CONCAT_WS('|', tracked_cols)).
- **Source:** legacy_patterns.sql Example 3 + databricks_patterns_reference.docx
- **Established:** run_id_002 / 2026-05-19

## CONV-006: L0 load pattern

- **Status:** active
- **Category:** platform
- **Convention:** COPY INTO from S3 or autoloader; full-load by file/event arrival; DELETE+INSERT prohibited except for L0 full-load; partition by source_load_date
- **Source:** user_instructions.docx + legacy_patterns.sql Example 1
- **Established:** run_id_002 / 2026-05-19
