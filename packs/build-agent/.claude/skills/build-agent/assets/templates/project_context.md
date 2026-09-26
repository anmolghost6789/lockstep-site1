# Project Context

> Provide project-specific information that applies to this particular build run. This covers the scope, timeline, deliverables, and any project-specific constraints or decisions that override enterprise or domain defaults.

## Project Overview

- **Project Name:** [e.g., Sales Data Warehouse - Phase 1]
- **Project Goal:** [e.g., Build a production-ready sales reporting layer from CRM and ERP data]
- **Current Phase:** [e.g., Initial build, Enhancement, Migration]
- **Timeline:** [e.g., 4 weeks, delivery by March 30]

## Scope

### In Scope

> What tables, layers, and artifacts should this build run produce?

- [e.g., L0 staging tables for customer and order data]
- [e.g., L2 customer dimension with SCD2]
- [e.g., L2 product dimension with full load]
- [e.g., L3 sales fact table with incremental load]
- [e.g., DQ checks for all tables]
- [e.g., dbt-compatible tests for L2 and L3]

### Out of Scope

> What is explicitly excluded from this build?

- [e.g., L4 aggregation / mart layer — planned for Phase 2]
- [e.g., Real-time streaming pipeline — not in scope]
- [e.g., Dashboard or reporting layer]

## Target Platform Details

> If these differ from enterprise defaults, specify them here.

- **Platform:** [e.g., Snowflake]
- **Warehouse:** [e.g., ANALYTICS_WH]
- **Role:** [e.g., TRANSFORM_ROLE]
- **Target Schema(s):** [e.g., edw_staging, edw_dw]
- **Target Database Pattern:** [e.g., edw_db_{env}]

## Output Expectations

### Artifact Types Required

| Artifact | Required | Notes |
|----------|----------|-------|
| DDL | Yes | CREATE OR REPLACE TABLE statements |
| DML | Yes | INSERT/MERGE transformation logic |
| DQ | Yes | SQL-based DQ check scripts |
| Tests | Optional | dbt-style or standalone SQL tests |

### Output Organization

> How should the generated artifacts be organized in the output folder?

- [e.g., One folder per table under `generated/`]
- [e.g., DDL, DML, DQ, and tests as separate files per table]
- [e.g., Flat structure with naming convention: `{table_name}_ddl.sql`, `{table_name}_dml.sql`, etc.]

### File Naming Convention

- [e.g., `{table_name}_ddl.sql`]
- [e.g., `{table_name}_dml.sql`]
- [e.g., `{table_name}_dq.sql`]
- [e.g., `{table_name}_test.sql`]

## Project-Specific Decisions

> Record any decisions made specifically for this project that the agent should respect. These override enterprise or domain defaults when they conflict.

| Decision | Rationale | Made By | Date |
|----------|-----------|---------|------|
| [e.g., Use MERGE for SCD2 instead of DELETE+INSERT] | [e.g., Snowflake MERGE is more efficient for our volume] | [e.g., Lead Architect] | [e.g., 2025-01-15] |
| [e.g., Skip DQ for L0 staging tables] | [e.g., DQ is applied at L1 after initial cleansing] | [e.g., Project Lead] | [e.g., 2025-01-20] |

## Dependencies and Prerequisites

> List anything this build depends on that must exist or be true before the generated artifacts can run.

- [e.g., Reference tables (ref_country, ref_currency) must be pre-loaded]
- [e.g., Staging tables must be populated by upstream pipeline before L2/L3 loads run]
- [e.g., Unknown member rows (-1) must exist in all dimension tables]

## Team and Contacts

| Role | Name | Notes |
|------|------|-------|
| Data Engineer | [name] | Primary build engineer |
| Architect | [name] | Review and approval |
| Business Analyst | [name] | Business rule clarification |
| QA | [name] | Testing and validation |

## Additional Notes

> Any other project-specific context that does not fit the sections above.

- [e.g., Client prefers verbose comments in generated SQL]
- [e.g., All generated code must be compatible with dbt compilation]
- [e.g., This is a migration from legacy Oracle DW — legacy SQL examples in inputs/ show current patterns]
