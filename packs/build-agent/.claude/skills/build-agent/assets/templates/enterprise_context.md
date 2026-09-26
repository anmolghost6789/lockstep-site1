# Enterprise Context

> Provide enterprise-wide information that applies across all projects and domains within the organization. This helps the agent understand the broader technical landscape and standards.

## Organization Overview

- **Organization Name:** [e.g., Acme Corp]
- **Industry:** [e.g., Retail, Pharma, Financial Services, Healthcare]
- **Data Team Size:** [e.g., 5 engineers, 2 architects]

## Enterprise Data Platform

- **Cloud Provider:** [e.g., AWS, Azure, GCP]
- **Data Platform:** [e.g., Snowflake, Databricks, BigQuery, Synapse, Redshift]
- **SQL Dialect:** [e.g., Snowflake SQL, Spark SQL, T-SQL, BigQuery SQL]
- **Orchestration Tool:** [e.g., Airflow, dbt Cloud, Azure Data Factory, Prefect]
- **Version Control:** [e.g., GitHub, GitLab, Bitbucket]
- **CI/CD Pipeline:** [e.g., GitHub Actions, Jenkins, Azure DevOps]

## Enterprise Data Architecture

### Layer Definitions

> Define what each layer means in your organization. Common patterns shown below — edit to match yours.

| Layer | Name | Purpose |
|-------|------|---------|
| L0 | Raw / Landing | Raw file or API ingest. No transformation. |
| L1 | Staging / Work | Light cleansing, type casting, deduplication. |
| L2 | Conformed / Dimension | Business-modeled dimensions and reference tables. |
| L3 | Integrated / Fact | Fact tables joining dimensions and business measures. |
| L4 | Aggregated / Mart | Pre-aggregated reporting or analytics tables. |

### Schema Naming Convention

> How schemas are organized across layers and environments.

| Layer | Schema Pattern | Example |
|-------|---------------|---------|
| L0 | `{project}_raw` | `sales_raw` |
| L1 | `{project}_staging` | `sales_staging` |
| L2 | `{project}_dw` | `sales_dw` |
| L3 | `{project}_dw` | `sales_dw` |
| L4 | `{project}_mart` | `sales_mart` |

### Database / Environment Pattern

- **Pattern:** [e.g., `{project}_db_{env}` where env = dev, uat, prod]
- **Environments:** [e.g., dev, uat, prod]

## Enterprise Coding Standards

### Naming Conventions

- **Tables:** [e.g., snake_case, prefixed with d_ for dimensions, f_ for facts, stg_ for staging]
- **Columns:** [e.g., UPPER_SNAKE_CASE]
- **Surrogate Keys:** [e.g., {TABLE_NAME}_SK]
- **Business Keys:** [e.g., keep source system name]
- **Audit Columns:** [e.g., INRT_DT, INRT_BY, UPDT_DT, UPDT_BY, CYCL_TIME_ID]

### Standard Audit Columns

> List the audit columns that every table must have.

| Column | Data Type | Description |
|--------|-----------|-------------|
| INRT_DT | TIMESTAMP | Record insert timestamp |
| INRT_BY | VARCHAR | Insert user or process |
| UPDT_DT | TIMESTAMP | Record update timestamp |
| UPDT_BY | VARCHAR | Update user or process |
| CYCL_TIME_ID | VARCHAR | Batch / cycle identifier |

### SQL Style Preferences

- **Keyword casing:** [e.g., UPPERCASE for SQL keywords]
- **Indentation:** [e.g., 4 spaces]
- **CTE vs subquery preference:** [e.g., prefer CTEs]
- **MERGE vs DELETE+INSERT for SCD2:** [e.g., MERGE]
- **Comment style:** [e.g., block comment header, inline for complex logic]

## Enterprise DQ Standards

### DQ framework (pick one)

> The agent emits DQ artifacts in the format matching the selected framework. If this line is blank, `sql_procedural` is the default.

- **DQ framework:** [pick one — see options below]

| Option | What the agent emits | Typical use |
|---|---|---|
| `sql_procedural` | `.sql` files with `SELECT COUNT(*) ...` check patterns; write results to a `dq_results` table | Teams running native SQL on Snowflake/BigQuery/Synapse/Databricks/Redshift without a dedicated DQ tool |
| `dbt_tests` | `schema.yml` generic tests (not_null, unique, accepted_values, relationships) + singular `.sql` test files under `tests/` for complex rules | Teams using dbt Core or dbt Cloud |
| `great_expectations` | `.py` expectation suite stubs plus an `expectations_config.yml` referencing the suites | Teams using Great Expectations for data validation |
| `deequ` | Scala DSL constraint stubs (`.scala`) using `VerificationSuite` and `Check` | Teams running Spark-based Deequ checks on Databricks/EMR |
| `custom` | The agent will ask for the exact emission format at the first DQ artifact | Any in-house DQ framework |

### Test framework (pick one, optional — defaults to the DQ framework if blank)

- **Test framework:** [pick one — see options below]

| Option | What the agent emits |
|---|---|
| `sql_assertions` | `.sql` files with assertion SELECTs that fail on data issues |
| `dbt_tests` | dbt tests (singular + generic) — same structure as DQ artifacts |
| `great_expectations` | Expectation suites marked as tests |
| `custom` | Agent asks for format |

### Other DQ standards

- **Criticality levels:** C (Critical) = must pass for load to proceed, NC (Non-Critical) = log and continue
- **Threshold handling:** [e.g., percentage of rows allowed to fail before rule triggers]
- **DQ result logging:** [e.g., write to dq_results table, alert via Slack]

## Security and Compliance Notes

> Any relevant notes about data handling, masking, PII treatment, or regulatory constraints that affect how generated code should handle sensitive data.

- [e.g., PII columns must use dynamic masking in prod]
- [e.g., No real data in dev — use synthetic]
- [e.g., GDPR applies — customer deletion must cascade]
