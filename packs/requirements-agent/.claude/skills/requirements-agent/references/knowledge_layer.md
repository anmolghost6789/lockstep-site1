# Local requirements knowledge graph

The linked bundle under `outputs/00_state/knowledge/` follows OKF v0.1.
Markdown is canonical; `state.json` is a derived machine index. Never create a
graph JSON file, database, embedding index, or copied retrieval packet.

## Progressive disclosure and layout

- `index.md` declares `okf_version: "0.1"` and links to descriptive routing
  indexes.
- `log.md` records concise chronological semantic changes.
- `sources/index.md` routes to thin provenance concepts;
  generation does not read this route normally.
- `coverage/index.md` routes to non-captured source-locator exceptions grouped
  by exact input category; source pages combine them with concept Evidence.
- Semantic directories are chosen from the input domain. Their `index.md` files
  are generated recursively from canonical concept files.
- Runs choose dynamically between standalone concept files and cohesive
  `Requirements Collection` pages whose H2 entity sections remain exact graph
  and retrieval units.

Only `sources/`, `coverage/`, the root index, and `log.md` have fixed roles. Do not create a
universal empty folder taxonomy.

## Dynamic granularity

Group concise concepts when they share a real semantic route, lifecycle,
evidence neighborhood, and output use. Each H2 node still owns its evidence,
status, verification, relations, and downstream applicability. Use a standalone
file when one coherent multi-section narrative must be read or revised together,
or when it has an independent lifecycle boundary. Keep tightly coupled material
together when splitting would remove essential meaning, such as a use case and
its alternate flows or one coherent data contract. Never split or group by
sentence, selected deliverable, worker, numeric range, quota, or target size.

The result must preserve every decision-bearing requirement, constraint,
definition, threshold, exception, uncertainty, contradiction, and open
question without copying the source corpus wholesale.

Promote material into a separate canonical entity only when it needs at least
one independent graph responsibility: its own lifecycle/status/confidence,
downstream applicability, typed relationship target, contradiction, open-item
resolution, or independently verifiable normative obligation. Otherwise keep
the detail losslessly inside the nearest owning entity as a table row, list,
definition, example, field, alternate flow, or subsection with its source
locator. Comprehensive knowledge does not mean one node per source heading,
sentence, bullet, person, field, template instruction, or catalog row.

Prefer one cohesive entity containing a structured catalog when its members
share lifecycle and output use. Split a member into its own entity only when a
requirement or decision addresses it independently. This applies generically to
glossaries, stakeholder rosters, field inventories, KPI catalogs, source-system
attributes, process steps, and configuration lists. The owning entity's
Evidence accounts for every preserved locator, so consolidation must never
drop provenance or visible detail.

## First-class concept shape

Every semantic concept begins with this producer metadata:

```markdown
---
type: Functional Requirement
title: Validate customer eligibility
description: Validates eligibility before approval.
canonical_id: UC-FR-012
status: confirmed
confidence: high
outputs: [BRD, FRD, JIRA]
tags: [eligibility, validation]
---

# UC-FR-012 - Validate customer eligibility

## Statement

The system SHALL validate eligibility before approval.

## Evidence

- [SRC-004](../sources/SRC-004-policy.md) - policy section 4.1

## Verification

Approval is unavailable until the eligibility result is recorded.

## Relations

- depends_on: [FR-003](../validation/fr-003-validation.md#fr-003)
- satisfies: [BR-008](../business-rules/br-008-approval.md#br-008)
```

Required fields are `type`, `title`, `description`, `canonical_id`, `status`,
`confidence`, and non-empty selected `outputs`. Use an evidence-specific type;
do not label all concepts as generic topics. Add `tags`, `resource`,
`standalone_reason`, or `timestamp` only when the value is useful. Update a
timestamp only for a semantic change.

Route a concept only to deliverables that need its semantic body; never copy
all selected output IDs by default. The dynamic template and explicit source
instructions may override these normal roles:

- BRD: business outcomes, scope, stakeholders, capabilities, rules, KPIs, and
  business-significant constraints.
- FRD: functional behavior, use cases, data behavior, interfaces, business
  rules, and non-functional requirements needed to specify the solution.
- URS: user goals, roles, workflows, observable needs, constraints, and
  acceptance outcomes; omit implementation detail that users do not require.
- JIRA: independently implementable or verifiable work, dependencies, and
  acceptance context suitable for backlog execution.

Route each concept independently; routing a parent capability does not cover
its linked child obligations. Before committing extraction, audit every
`part_of`, `has_part`, `depends_on`, and `satisfies` neighborhood for the
selected outputs. When JIRA is selected, every in-scope implementable or
verifiable obligation needed to deliver a JIRA-routed capability (including
computations, rules, constraints, and quality attributes) must itself include
JIRA. Keep a linked child out of JIRA only when its semantic body is genuinely
non-executable context, not merely because the parent is already routed.

Knowledge completeness is independent of routing: preserve every material fact
in the graph even when it is intentionally inapplicable to one deliverable.
An exception coverage page represents exactly one input category. Record one
row per distinct source locator and meaning; link all affected concepts once in
that row instead of repeating the locator in duplicate rows.

Use stable globally unique IDs and one normative obligation per requirement
concept. Ground facts with a source-concept link and locator, or use assumption,
insufficient, or draft status. Allowed relationship types are `depends_on`,
`part_of`, `has_part`, `contradicts`, `supersedes`, `superseded_by`,
`implemented_by`, `satisfies`, and `related_to`. Every target must exist.
Resolve link paths from the concept's actual directory: one-level semantic
routes use `../sources/`, while nested routes require another `../`. Examples
do not define a fixed directory depth.

ID families carry semantic meaning, not worker ownership or deliverable routing.
Preserve valid source-defined IDs and existing graph families. For concepts
without a source-defined scheme, choose a short family from the concept's actual
meaning and use it consistently; never force every corpus into a fixed taxonomy.

### Preflight-safe authoring contract

Apply these producer constraints while planning the ID map, before writing. They
are deliberately listed here so semantic authors never need to inspect validator
code or discover structural rules through a repair loop.

- Every canonical entity ID is uppercase, uses hyphen-separated alphanumeric
  segments of 1-12 characters, and ends in a numeric segment of 1-8 digits.
  When splitting a concept, allocate another numeric ID; never append a letter
  after the final number. Examples:
  `BR-001`, `KPI-CAT-001`, `R-CAP-JIRA-001`. Preserve a source-defined ID only
  when it has this graph-safe shape; otherwise record the original ID in the
  concept prose/evidence and assign a stable graph ID.
- A standalone page's H1 begins with its exact `canonical_id`. A
  `Requirements Collection` omits page-level `canonical_id`, `status`,
  `confidence`, and `outputs`; each H2 entity carries its own valid ID and the
  per-node lines shown below. Links target that exact entity anchor.
- Each relationship line under `## Relations` uses an allowed type followed by
  one or more existing canonical IDs in Markdown links. Descriptive labels
  without a canonical ID are prose, not graph edges.
- Every concept declares at least one meaningful outbound relation or a concise
  `standalone_reason`. Do not rely only on a future sibling-owned incoming edge;
  this keeps each locally authored graph fragment independently traversable.
- A requirement entity owns one independently verifiable normative obligation.
  Put one `SHALL` obligation in its `## Statement`; split separate obligations
  into separate entities. Evidence, verification, and relation prose may refer
  to that obligation without creating another entity.
- Do not mint an entity merely to make a source bullet independently searchable.
  Keep contextual or catalog detail inside its owning entity unless it meets the
  first-class promotion rule above.
- Run the read-only global `validate` after shapes, evidence links, and
  cross-source relationships are internally consistent. Repair exact returned
  semantic issues without reading validator implementation.

Use this shape when cohesive concepts share one collection page:

```markdown
---
type: Requirements Collection
title: Eligibility measures
description: Evidence-backed eligibility measures and thresholds.
tags: [eligibility, measures]
---

# Eligibility measures

## KPI-001 - Adult acceptance rate

Type: KPI
Status: confirmed
Confidence: high
Deliverables: BRD, FRD

### Statement

Accepted adult applications divided by evaluated applications.

### Evidence

- [SRC-004](../sources/SRC-004-policy.md) - policy section 4.1

### Relations

- satisfies: [BR-008](../business-rules/rules.md#br-008)
```

## Source coverage contract

Classify every material locator while reading a changed source. Put captured
meaning only in the owning concept's `Evidence`; this is the canonical
concept-to-source edge. When a source category has non-captured locators, author
one `coverage/*.md` page for that exact category. Do not create an empty page,
one page per source, or one monolithic corpus file. Each exception page has OKF
metadata with type `Source Coverage Collection` and this canonical table:

```markdown
## Source accounting

| Source | Locator | Meaning | Concepts | Disposition |
|---|---|---|---|---|
| [SRC-004](../sources/SRC-004-policy.md) | Section 4.2 | Workshop scheduling | none | context-only |
```

Use `context-only`, `contradiction`, `duplicate`, `out-of-scope`, `superseded`,
or `unresolved`. Contradiction, duplicate, and superseded rows require concept
links backed by Evidence from the same source and locator. Never author a new
`captured` row. Commit derives captured rows from concept Evidence, merges exact
exception locators, validates the resolved view, and projects it onto each
generated `SRC-*` page. A legacy captured row remains readable only when its
concepts have canonical Evidence in that source; it is ignored in projection.
Every active source must resolve to at least one captured Evidence or explicit
exception row. The model never edits source pages one by one.

## Retrieval contract

Generation runs `generation-context` for its compact route receipt, then
`retrieve-context` for bounded semantic groups. The default `authoring` view
preserves exact obligation prose, evidence IDs, insufficiency markers, and typed
relations while omitting graph-only paths and routing metadata; `--view full`
is reserved for explicit knowledge repair.

Retrieval starts from exact dirty or applicable concept IDs; free-form revisions
may use lexical query seeding. It expands at most one relationship hop, batches
selected concepts, and keeps context-only nodes separate from nodes that
authorize document edits. Do not load every page; broaden only when returned
context is insufficient for a named concept or decision.

Normal generation reads zero raw sources and zero source-concept pages. If a
concept is missing, ambiguous, conflicted, or insufficient, return the specific
ID to extraction. Evidence repair may read only the cited source locator, update
the canonical concept and source coverage, revalidate, and resume.
