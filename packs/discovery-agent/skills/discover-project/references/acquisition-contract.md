# Source profiles and data acquisition contracts

Use this reference whenever the resolved facets include `acquisition`.

## Model

Create:

1. one `source_system_profile` per relevant source/environment;
2. one `acquisition_contract` per independently deployable feed or ingestion group;
3. one `ingestion_spec` derived from each acquisition contract that moves or exposes data;
4. a table/file/topic/API asset concept only when it has independent semantics, evidence, risk, lifecycle, or an override.

Do not copy an enterprise catalog into OKF. Link catalog identifiers and keep a compact asset matrix inside the acquisition contract. For files, the asset is a logical feed or path pattern, not each file instance.

## Source system profile

Use `de_agents.role: source_system_profile` and this top-level structure:

```yaml
source_system:
  identity_ownership: {status: supported, gaps: []}
  connectivity_access: {status: supported, gaps: []}
  structure_scale: {status: partial, gaps: [Peak change rate is not observed.]}
  change_capabilities: {status: supported, gaps: []}
  security_governance: {status: supported, gaps: []}
  operational_constraints: {status: supported, gaps: []}
```

Describe engine/service/version, environment, owner, connection route, secret reference, privileges, network path, accessible namespace, approximate scale, source-load windows, CDC/change mechanisms, classification, retention, maintenance, and known connector limitations. Never store credentials.

## Acquisition contract

Use:

```yaml
de_agents:
  role: acquisition_contract
  contract_version: "1.0"
  contract_status: assessed
acquisition:
  source_scope: {status: supported, gaps: []}
  target_mapping: {status: partial, gaps: [Target catalog is not approved.]}
  delivery: {status: supported, gaps: []}
  change_capture: {status: supported, gaps: []}
  schema: {status: supported, gaps: []}
  quality_reconciliation: {status: partial, gaps: [Business totals need an owner.]}
  security_governance: {status: supported, gaps: []}
  operations_recovery: {status: supported, gaps: []}
```

Allowed contract status progression:

`assessed` → `feasible` → `approved` → `implementation-ready` → `deployed`

Discovery may recommend and reach `feasible`. Only mark `approved` when the authorized design decision is recorded. Later DE Agents enrich the same concept rather than creating a competing contract.

## Required content

Within the structured sections and body, capture:

- business purpose, source owner, consumers, asset selection/rejection;
- source FQN/URI and target mapping;
- connector/pattern candidates and recommendation;
- snapshot, append, incremental, CDC, streaming, federation, or sharing semantics;
- cadence, freshness, latency, volume, change rate, file/event ordering;
- grain, keys, cursor/sequence, filters, selected columns, deletes, history/SCD;
- schema inference, contract, drift/evolution, rescued/quarantine behavior;
- initial load, backfill, late data, replay, checkpoint/high-water mark, idempotency;
- reconciliation, quality rules, tolerances, acceptance owner;
- classification, residency, retention, encryption, access boundaries;
- scheduling, dependencies, failure handling, monitoring, alerts, recovery, support;
- connector/source limitations, cost/load implications, evidence, contradictions, gaps.

Use `unknown` in prose and a `partial` or `missing` section status when a value is not known. Never guess a cursor, key, deletion mode, cadence, or target.

Lakeflow query-based ingestion requires table-level cursor, key, deletion, history, and destination choices. Auto Loader requires feed-level schema/checkpoint/evolution decisions. ODCS can be linked when a provider-consumer data contract exists; the acquisition contract remains the engineering handoff for obtaining the data.

## Ingestion specification

The acquisition contract is the evidence-backed engineering decision. The ingestion specification
is its compact machine-readable projection for Design and Build. Do not put credentials in it and
do not create a competing narrative.

Use:

```yaml
de_agents:
  canonical_id: ingestion.commercial-postgres.current
  role: ingestion_spec
  observation: proposed
  source_revision_ids: []
  spec_version: "1.0"
  spec_status: candidate
  derived_from: [acquisition.commercial-postgres.current]
ingestion:
  gaps:
    - Primary keys and delete behavior are not yet evidenced.
  sources:
    - connection_id: commercial_postgres_main
      source_type: rdbms
      engine: postgresql
      host: "${var.pg_host}"
      port: 5432
      database: commercial_db
      connection_name: "${var.connection_name}"
      secret_reference: commercial-postgres-creds
  datasets:
    - connection_id: commercial_postgres_main
      source_schema: crm
      source_table: hcp_profile
      destination_table: raw_hcp_profile
      load_type: incremental
      watermark_column: updated_at
```

Allowed specification lifecycle:

`candidate` → `implementation-ready` → `approved` → `deployed`

Keep a specification at `candidate` while material values are missing. A candidate must name its
gaps and cannot be exported. `approved` and `deployed` require a `verified` entry recording the
authorized reviewer or deployment verification.

For `implementation-ready`, clear `ingestion.gaps` and capture:

- a Databricks connection reference plus RDBMS engine and database when applicable;
- an optional `asset_type` (`table` by default, or `file`, `stream`, `api`, or `share`);
- source schema/table, file URI and format, topic, or logical API object as appropriate;
- destination catalog/schema/table;
- load type and connector/pattern selection;
- a validated watermark for incremental loads;
- primary keys for non-append incremental merge behavior;
- schedule and freshness-driving cadence;
- explicit delete handling;
- schema-evolution behavior;
- reconciliation checks and acceptance owner;
- checkpoint/state and replay strategy.

For CDC, also capture primary keys and `change_capture.method`. For file feeds, use one logical
path or pattern per feed rather than enumerating file instances; file incrementality is governed by
checkpoint/state and schema-evolution decisions, not an RDBMS watermark.

Example implementation-ready dataset:

```yaml
connection_id: commercial_postgres_main
source_schema: sales
source_table: prescription_transaction
destination_catalog: "${var.destination_catalog}"
destination_schema: "${var.destination_schema}"
destination_table: raw_rx_transaction
load_type: incremental
watermark_column: updated_at
watermark_validation: {status: supported, gaps: []}
primary_keys: [prescription_transaction_id]
schedule: {mode: periodic, interval: 1, unit: hours}
delete_handling: {mode: soft, condition: "deleted_at IS NOT NULL"}
schema_evolution: {mode: add_new_columns}
reconciliation:
  checks: [row_count, sum_quantity]
  owner: Commercial data owner
recovery:
  checkpoint_or_state: Lakeflow-managed ingestion state
  replay_strategy: Reset and replay an approved source window
```

Use one specification for datasets that share a deployable connection and operational pattern.
Split specifications when ownership, deployment lifecycle, connector, security boundary, or
operational behavior differs. Route every active specification to both Design and Build in the
context manifest.

After the full OKF profile validates, export an implementation-ready specification:

```text
TOOL export-ingestion-config --project-root PROJECT_ROOT \
  --canonical-id ingestion.commercial-postgres.current
```

The exporter writes a plain YAML projection containing only `sources` and `datasets`. It is a
neutral DE Agents handoff, not a claim that its keys exactly match every Databricks connector API.
Build maps it to the current approved Databricks Declarative Automation Bundle or API contract.

Primary references:

- [Lakeflow query-based connector reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/query-based-reference)
- [Auto Loader schema inference and evolution](https://docs.databricks.com/gcp/en/ingestion/cloud-object-storage/auto-loader/schema)
- [Open Data Contract Standard](https://docs.datacontract.com/open-data-contract-standard)
