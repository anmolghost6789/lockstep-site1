# DE Agents OKF v0.2 profile

This profile adds discovery conventions without closing the Open Knowledge Format ontology.

## Bundle rules

- `knowledge/index.md` is the root navigation page. Its frontmatter is exactly:

  ```yaml
  ---
  okf_version: "0.2"
  ---
  ```

- `knowledge/log.md` is newest-first and uses `## YYYY-MM-DD` headings.
- Every other `.md` file is a concept. Its bundle-relative path without `.md` is its OKF concept ID.
- Each concept has parseable YAML frontmatter and a non-empty `type`.
- Use Markdown links with bundle-absolute paths, for example `[Orders](/data/orders.md)`.
- Unknown OKF fields and concept types are allowed. Preserve them.

## Recommended concept frontmatter

```yaml
---
type: data-asset
title: Curated orders
description: Governed order-level dataset used for revenue reporting.
status: draft
tags: [orders, revenue]
sources:
  - id: source-orders-ddl-r2
    resource: evidence://sha256/<digest>/orders.sql
    description: Source DDL revision 2
generated:
  by: de-discovery/0.3.0
  at: 2026-07-27T10:00:00Z
de_agents:
  canonical_id: data.orders.curated
  role: data_asset
  observation: observed
  source_revision_ids: [source-orders-ddl-r2]
---
```

The top-level `type` is required by OKF. `de_agents` is an extension namespace. Supported extension fields are:

- `canonical_id`: stable semantic identity across file moves;
- `role`: stable machine-discovery role;
- `observation`: `observed`, `reported`, `inferred`, or `proposed`;
- `source_revision_ids`: evidence revisions that may trigger reconsideration;
- `supersedes`: canonical IDs replaced by this concept;
- `applies_to`: referenced systems, assets, or lifecycle stages;
- `readiness_target`: the configured `discovery-only`, `requirements-ready`, or `design-ready` gate on the context manifest and readiness assessment;
- `readiness_result`: `supported`, `conditional`, or `blocked` on the readiness assessment;
- `boundary_status`: `active` on the current discovery boundary;
- `created_resource_ids`: every discovery-created resource as `<type>:<name>` on the context manifest.
- `engagement_archetypes`, `required_facets`, and `facet_coverage`: resolved project coverage on the context manifest;
- `downstream_context`: stable canonical-ID routing lists for Requirements, Design, and Build;
- `contract_version` and `contract_status`: acquisition-contract lifecycle;
- `spec_version`, `spec_status`, and `derived_from`: ingestion-spec format, lifecycle, and source acquisition-contract IDs;
- `migration_disposition` and `migration_complexity`: evidenced migration-unit assessment.

Do not store subjective confidence scores. Represent trust with provenance, verification, lifecycle status, contradictions, and evidence coverage.

## Material claims

Use claim citations when a paragraph contains facts that affect scope, semantics, design, security, cost, or acceptance:

```markdown
The curated table is updated every two hours.[^jobs-observation]

[^jobs-observation]: Observed from the production job definition on 2026-07-27.
```

The footnote label must match a `sources[].id`. `resource` should resolve to:

- `evidence://sha256/<digest>/<filename>` for a local immutable snapshot;
- an immutable or versioned remote URI;
- a Databricks object URI plus observation timestamp and workspace identity;
- a concept link for a derived statement, while the upstream concept retains primary evidence.

## Required roles

Exactly one non-deprecated concept must have each role:

- `context_manifest`;
- `discovery_boundary`;
- `readiness_assessment`.

Create other roles only when useful, for example `open_questions`, `decision`, `business_term`, `data_asset`, `data_flow`, `control`, `risk`, or `quality_observation`.

Conditional profile roles:

- the `acquisition` facet requires one or more `source_system_profile`, `acquisition_contract`, and `ingestion_spec` concepts;
- `migration-modernization` requires one `migration_assessment` and one or more `migration_unit` concepts;
- a `design-ready` migration also requires one proposed `migration_plan`.

## Context manifest

The context manifest is the downstream DE Agent entrypoint. It contains:

- objective and requested readiness target;
- engagement archetypes, resolved facets, and per-facet coverage;
- current boundary and explicit exclusions;
- links grouped by downstream concern, not by folder name;
- canonical-ID routing for `requirements`, `design`, and `build`;
- source-revision summary and evidence coverage;
- authoritative concepts and unresolved contradictions;
- readiness result and blocking gaps;
- Databricks resources created;
- safe refresh instructions;
- generated timestamp and discovery plugin version.

It directly links every conditional profile concept required by the engagement. Every active ingestion specification is routed to Design and Build by canonical ID. Specialized contract structure is defined in the acquisition and migration references.

It must point, not duplicate. A downstream agent should load the manifest, then only the linked concepts relevant to its task.

The bundle is not profile-complete until `log.md` has at least one newest-first dated entry and every registered source revision has an explicit review disposition.
