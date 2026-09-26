# Decisions

> Durable decisions made during runs. Each decision should capture rationale and status. Later decisions must mark earlier ones as superseded when they replace them.

<!-- Example entry format:

## [Decision ID]: [Short Title]

- **Status:** active | superseded | retired
- **Decision:** [What was decided]
- **Rationale:** [Why]
- **Made by:** [User, agent, or collaborative]
- **Run ID:** [Which run this was decided in]
- **Date:** [When]
- **Supersedes:** [Decision ID, if replacing an earlier decision]
- **Impact:** [What tables, phases, or artifacts this affects]
- **Notes:** [Any additional context]

-->

## DEC-001: Databricks Lakehouse on AWS as target platform

- **Status:** active
- **Decision:** All generated SQL artifacts use Spark SQL (Databricks Runtime 14.3 LTS). Pipeline artifacts use Databricks Workflows YAML.
- **Rationale:** Confirmed by enterprise_context.docx (Helixor EDAO standard) and user selection at run_id_002 scope selection.
- **Made by:** Collaborative (enterprise context + user)
- **Run ID:** run_id_002
- **Date:** 2026-05-19
- **Supersedes:** N/A
- **Impact:** All DDL, DML, DQ, Pipeline, Tests for this run

## DEC-002: All five artifact families in scope for run_id_002

- **Status:** active
- **Decision:** DDL + DML + DQ + Pipeline + Tests selected. Pipeline platform = Databricks.
- **Rationale:** User selected "all" at scope selection.
- **Made by:** User
- **Run ID:** run_id_002
- **Date:** 2026-05-19
- **Supersedes:** N/A
- **Impact:** All phases
