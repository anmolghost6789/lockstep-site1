# Discovery method

## Investigation funnel

Discovery is a relevance problem before it is a scale problem.

1. **Seed:** start with the project objective, named systems, terms, owners, and supplied artifacts.
2. **Neighborhood:** inspect metadata directly surrounding those seeds: matching names/descriptions, immediate schemas, known producers/consumers, recent queries, and one-hop lineage.
3. **Shortlist:** rank candidates from evidence and inspect only the configured maximum.
4. **Deep evidence:** collect schema, constraints, aggregate profile, lineage, operational history, and ownership for shortlisted assets.
5. **Expansion:** widen one boundary dimension only when an explicit readiness gap remains.

Do not use `LIMIT` as a substitute for metadata filtering. Record excluded candidates and why the investigation stopped.

## Candidate scoring

Score each component independently and retain the reason:

| Component | Range | Question |
|---|---:|---|
| Objective relevance | 0–5 | Does evidence connect the asset to the stated outcome or business terms? |
| Seed proximity | 0–4 | Is it named, directly referenced, or one dependency hop from a seed? |
| Authoritative use | 0–3 | Is it governed, owned, or demonstrably used by the relevant process? |
| Structural fit | 0–3 | Do grain, keys, fields, and temporal coverage fit the need? |
| Operational fitness | 0–2 | Is freshness, availability, and data quality adequate for investigation? |
| Evidence risk | 0 to −5 | Is relevance contradicted, stale, inaccessible, duplicated, or sensitive? |

`priority = sum(component scores)`.

Compare candidates by component vector, not total alone. A high total cannot erase a severe evidence-risk condition. The context manifest must state the configured shortlist cutoff and why near-cutoff assets were included or excluded.

## Boundary expansion

Request expansion only when all are true:

- a named readiness criterion remains unsupported;
- existing in-boundary evidence cannot close it;
- a specific adjacent system, schema, or lineage hop is likely to close it;
- cost, data sensitivity, and requested depth are known.

Ask with:

```text
Gap: <unsupported criterion>
Current evidence: <what was checked>
Requested expansion: <exact system/catalog/schema/assets and depth>
Expected value: <what decision it should unlock>
Operations: <read/profile/create; row access if any>
Cost/sensitivity: <known limits>
Fallback if declined: <assumption, deferral, or blocked outcome>
```

Approval expands only the named boundary. Update the boundary concept before work begins.

## Promotion and versioning

- A changed source creates a new immutable source revision.
- A concept is `draft` while material contradictions or unverified inferences remain.
- A concept may be `stable` when its material claims are source-linked and reviewed or directly observed.
- A concept becomes `deprecated` when superseded; retain it and link the successor.
- Enterprise- or domain-reusable knowledge is promoted by moving or copying the concept into the governed bundle chosen by the organization, preserving canonical ID, provenance, and supersession links. Discovery must propose promotion; it must not silently rewrite a shared bundle.
- Git history versions authored knowledge. Content hashes version captured evidence. Neither replaces the other.

## Change impact

When an input hash changes:

1. register the new revision;
2. find concepts whose `sources[].resource` or `de_agents.source_revision_ids` point to the prior revision;
3. mark only those concepts for reconsideration;
4. follow their explicit concept links to identify downstream impacts;
5. preserve unaffected concepts;
6. record accepted, rejected, and deferred changes in `log.md`.
