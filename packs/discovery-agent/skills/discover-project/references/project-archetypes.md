# Project archetypes and discovery facets

Classify the engagement before deep discovery. Select every applicable archetype; a legacy migration that also onboards source data normally uses both `migration-modernization` and `source-onboarding`.

## Supported archetypes

| Archetype | Typical work |
|---|---|
| `general` | Initial assessment when the exact delivery shape is not yet known |
| `greenfield-data-product` | New analytical product, warehouse/mart, semantic product, ML/AI data foundation |
| `source-onboarding` | Batch, files, APIs, CDC, streaming, replication, federation, or shared-data acquisition |
| `brownfield-change` | Extend or replace an existing pipeline, model, report, interface, or business rule |
| `migration-modernization` | Legacy warehouse/ETL migration, consolidation, refactor, or re-architecture |
| `platform-modernization` | Databricks/cloud/workspace/catalog/runtime/tooling modernization |
| `data-sharing` | Internal/external sharing, clean-room, marketplace, reverse-delivery, or consumer integration |
| `quality-reliability-remediation` | Data quality, incident, reconciliation, observability, recovery, or control remediation |
| `governance-compliance` | Classification, ownership, lineage, retention, privacy, audit, or access remediation |
| `performance-cost-optimization` | Workload performance, capacity, latency, reliability, or cost optimization |
| `decommission-archive` | Dataset, pipeline, platform, report, retention, archival, or source retirement |

Treat master/reference data, streaming, IoT, SaaS ingestion, M&A consolidation, reverse ETL, and Databricks-to-Databricks work as combinations of these archetypes instead of adding one-off workflows.

## Facets

Resolve the archetypes into only the facets needed for the named decision:

- `business`: outcome, value, scope, stakeholders, semantics, acceptance;
- `landscape`: systems, owners, environments, dependencies, usage;
- `data`: grain, schema, keys, history, scale, classification;
- `acquisition`: source access, selection, ingestion semantics, state, replay;
- `processing`: rules, transformations, orchestration, state, failure behavior;
- `consumption`: consumers, serving interfaces, reports, extracts, sharing;
- `quality`: profiling, rules, reconciliation, observability, issue history;
- `governance`: ownership, security, privacy, retention, lineage, audit;
- `operations`: schedules, SLAs/SLOs, monitoring, recovery, support;
- `platform`: environments, network, identity, compute, deployment constraints;
- `economics`: current/target cost drivers, capacity, licensing, TCO assumptions;
- `change`: migration, coexistence, cutover, rollback, decommissioning, impact.

Record every resolved facet and its `supported`, `partial`, `missing`, or `not_applicable` coverage in the context manifest. A facet is a discovery lens, not a required folder or report.

## Applicability rules

1. Add `source-onboarding` whenever data must move from a source into Databricks.
2. Add `data-sharing` when Databricks is a provider or consumer across an organizational boundary.
3. Add `quality-reliability-remediation` when the initiating problem is incorrect, late, missing, duplicated, or unrecoverable data.
4. Add `governance-compliance` when classification, retention, lineage, privacy, audit, or access is a material driver.
5. Add `decommission-archive` when success includes shutting down or retaining a legacy asset.
6. Use a custom archetype only when none of the broad types fits; declare explicit `required_facets`.

The Databricks reference architectures cover source, ingest, transform, query/process, serve, analysis, storage, sharing, batch, streaming/CDC, federation, BI, ML/AI, and operational applications. The well-architected framework adds operational excellence, security, reliability, performance, cost, governance, and interoperability. Use these as coverage checks, not as a mandatory target design.

Primary references:

- [Databricks reference architectures](https://docs.databricks.com/aws/en/lakehouse-architecture/reference)
- [Databricks well-architected framework](https://docs.databricks.com/aws/en/lakehouse-architecture/well-architected)
- [Batch and streaming semantics](https://docs.databricks.com/aws/en/data-engineering/batch-vs-streaming)
