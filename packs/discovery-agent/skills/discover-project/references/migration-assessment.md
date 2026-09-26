# Migration and modernization assessment

Use this reference for `migration-modernization`. Add `source-onboarding` when source data must move into Databricks.

## Migration unit

Assess workloads, not isolated tables. A migration unit is the smallest connected set of data, code, orchestration, controls, and consumers that can be migrated, validated, cut over, rolled back, and decommissioned together.

Start from business capabilities and active consumers. Follow usage and dependencies only to the configured depth. Include unused assets as retirement candidates without deeply profiling them.

## Required concepts

Create one `migration_assessment`:

```yaml
migration_assessment:
  drivers_scope: {status: supported, gaps: []}
  estate_inventory: {status: partial, gaps: [Two scheduler exports are missing.]}
  dependencies: {status: supported, gaps: []}
  usage_disposition: {status: supported, gaps: []}
  compatibility: {status: partial, gaps: [Dynamic SQL needs manual review.]}
  target_mapping: {status: partial, gaps: [Compute policy is not approved.]}
  economics: {status: partial, gaps: [Current license allocation is unavailable.]}
  risks_assumptions: {status: supported, gaps: []}
```

Create one or more `migration_unit` concepts:

```yaml
de_agents:
  role: migration_unit
  migration_disposition: convert
  migration_complexity: high
migration_unit:
  scope: {status: supported, gaps: []}
  dependencies: {status: supported, gaps: []}
  disposition: {status: supported, gaps: []}
  data: {status: supported, gaps: []}
  code: {status: partial, gaps: [One stored procedure needs manual conversion.]}
  consumers: {status: supported, gaps: []}
  validation: {status: supported, gaps: []}
  cutover_rollback: {status: partial, gaps: [Business blackout window is unconfirmed.]}
```

Allowed dispositions are `retire`, `retain`, `federate`, `rehost`, `convert`, `refactor`, `redesign`, and `undecided`. Preserve the evidence and trade-off; do not let a complexity score choose the disposition.

For `design-ready`, create one proposed `migration_plan`:

```yaml
migration_plan:
  waves: {status: supported, gaps: []}
  sequencing: {status: supported, gaps: []}
  coexistence: {status: supported, gaps: []}
  validation: {status: supported, gaps: []}
  cutover_rollback: {status: partial, gaps: [Final approver is not assigned.]}
  decommission: {status: supported, gaps: []}
```

## Assessment method

1. Establish drivers, success measures, deadlines, coexistence, and decommission intent.
2. Inventory relevant schemas, tables, views, procedures, ETL code, schedules, consumers, controls, and operating history.
3. Build dependency-aware migration units.
4. Assess usage and recommend disposition.
5. Assess data movement through acquisition contracts.
6. Assess code/orchestration compatibility and manual-remediation risk.
7. Map current capabilities to target outcomes without treating proposals as approved.
8. Define schema, row/data, aggregate/business, performance, security, and operational validation.
9. Propose dependency-aware waves, parallel run, cutover, rollback, and retirement.

Use Lakebridge only for supported sources and phases. Its Analyzer works from exported code; its Profiler requires a supported live source and is currently experimental. Reconcile can support post-migration comparisons for supported systems. Record tool version, coverage, warnings, and excluded objects.

Primary references:

- [Databricks migration overview](https://docs.databricks.com/aws/en/migration)
- [Lakebridge overview and support matrix](https://databrickslabs.github.io/lakebridge/docs/overview/)
- [Lakebridge Analyzer](https://databrickslabs.github.io/lakebridge/docs/assessment/analyzer/)
- [Lakebridge Profiler](https://databrickslabs.github.io/lakebridge/docs/assessment/profiler/)
- [Lakebridge Reconcile](https://databrickslabs.github.io/lakebridge/docs/reconcile/)
