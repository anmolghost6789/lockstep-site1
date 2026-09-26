# Evidence, contradictions, and readiness

## Evidence model

Use the narrowest truthful observation class:

- `observed`: directly inspected system metadata, configuration, aggregate result, or immutable artifact;
- `reported`: stated by a person or supplied narrative;
- `inferred`: reasoned from linked observations; show the reasoning and alternatives;
- `proposed`: a future option or recommendation.

One concept may contain different claim classes. Put the concept's dominant class in `de_agents.observation` and label exceptions in prose.

Never silently merge contradictions. Create a contradiction or open-question concept that links both claims, explains impact, and names the owner or next check.

## Requirements-ready

Mark `supported` only when evidence covers:

- problem, desired outcomes, stakeholders, and decision owners;
- in-scope and out-of-scope capabilities;
- material business terms, rules, grain, identifiers, and time semantics;
- required inputs/outputs and known consumers;
- regulatory, security, privacy, retention, and access constraints;
- freshness, volume, latency, availability, and quality expectations where applicable;
- acceptance measures or an explicit owner to define them;
- assumptions, contradictions, dependencies, and open questions.

Requirements-ready does not require a chosen target architecture.

When acquisition is in scope, Requirements-ready also needs the required source/feed, business freshness, history, retention, quality, security, ownership, and consumer expectations. Detailed connector configuration may remain open unless it changes feasibility or scope.

When migration is in scope, Requirements-ready also needs migration drivers, bounded capabilities/workloads, consumers, continuity expectations, retention/decommission intent, success measures, and material constraints. It does not require final migration waves.

## Design-ready

Design-ready includes Requirements-ready plus evidence for:

- shortlisted source and target assets with comparison rationale;
- relevant schemas, keys, relationships, lineage, interfaces, and change patterns;
- aggregate data characteristics needed for design decisions;
- current ingestion, transformation, orchestration, operational, and failure behavior;
- target-platform constraints and approved integration patterns;
- identity, network, secret, access-control, and data-classification boundaries;
- recovery, observability, performance, cost, and deployment constraints;
- unresolved design decisions with owners and impact.

A legacy system need not be exhaustively documented. Evidence must be sufficient for the bounded product and chosen decisions.

When acquisition is in scope, Design-ready requires:

- a source-system profile and acquisition contract for every selected ingestion unit;
- selected assets and target mappings;
- feasible delivery pattern with keys/cursor/sequence, delete and history behavior;
- initial load, backfill, replay, checkpoint, idempotency, and late/out-of-order behavior;
- schema contract/evolution and quality/reconciliation behavior;
- security, retention, source-load, failure, monitoring, recovery, and ownership constraints.

When migration is in scope, Design-ready requires:

- dependency-aware migration units and evidenced dispositions;
- data, code, orchestration, consumer, control, and operating compatibility;
- source-target mappings and explicit manual-remediation risks;
- proposed waves, coexistence, validation, cutover, rollback, and decommission plan;
- current and target cost/capacity assumptions where they affect the choice.

External guidance may support feasibility and best-practice claims, but only observed or supplied project evidence can establish the client's current state.

## Discovery-only

Discovery-only is supported when the bundle has:

- a usable project brief;
- a documented boundary and evidence inventory;
- an initial current-state map;
- ranked candidate assets;
- material unknowns and a recommended next discovery increment.

## Readiness assessment shape

For each criterion record:

```yaml
criterion: source_asset_fit
status: partial
evidence:
  - /assets/orders.md
gaps:
  - Change-data-capture behavior is not yet observed.
owner: platform-owner
blocking: true
```

Allowed statuses: `supported`, `partial`, `missing`, `not_applicable`.

The overall result is:

- `supported` only when no required criterion is `partial` or `missing`;
- `blocked` when a missing or partial criterion prevents the requested next stage;
- `conditional` when remaining gaps have explicit owners and do not block the named decision.

Do not average criterion statuses into a percentage.
