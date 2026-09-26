# Requirements quality rubric

Apply this rubric to the actual evidence, selected outputs, and authoritative
templates. Do not import section numbers, personas, regulatory regimes, label
namespaces, or document conventions from a previous run.

## Knowledge quality

| Check | Pass condition |
|---|---|
| Source accounting | Every material source locator is captured, explicitly disposed, or identified as unresolved. |
| Fidelity | Concepts preserve exact meaning, qualifiers, thresholds, exceptions, decisions, and uncertainty. |
| Provenance | Evidence links resolve to the correct source and useful locator. |
| Atomicity | Each normative concept has one independently testable obligation. |
| Granularity | Nodes are detailed enough to stand alone without unnecessary physical fragmentation. |
| Connectivity | Typed relationships are meaningful, resolvable, and sufficient for traversal. |
| Applicability | Each concept routes to every selected template that consumes it and no unrelated output. |
| Conflict discipline | Contradictions, supersession, assumptions, and insufficient evidence remain explicit. |

## Output quality

| Check | Pass condition |
|---|---|
| Template fidelity | Required headings, ordering, table schemas, and fields from the selected template are preserved. |
| Coverage | Every applicable knowledge concept is represented at the appropriate point of use. |
| Correctness | Content agrees with validated knowledge and introduces no unsupported specificity. |
| Standards conformance | Content applies every context/guidance-derived concept it invokes — calculation and threshold definitions, naming/formatting conventions, compliance/security/retention rules, and template-required governance fields — exactly as captured in validated knowledge, with no silent deviation, omission, or reinterpretation. |
| Requirement quality | Obligations are necessary, clear, feasible, unambiguous, and verifiable. |
| Traceability | Document ownership links resolve through canonical graph IDs to source evidence. |
| Consistency | Terminology, quantities, actors, status, and dependencies agree within and across selected outputs. |
| Professional fitness | The artifact supports its intended business, specification, delivery, or review decision. |
| Uncertainty handling | Assumptions and gaps are visible where used and routed for resolution. |

Unless a selected template or run instruction states otherwise, all nine
Output quality checks carry equal weight in the scorecard. Standards-conformance
defects use the same severity tokens and callout skeleton as other output
defects (report_grammar.md §3.5); "Standards conformance" is the check name in
the title, not a distinct severity tag.

### Three lenses

Every Output quality check answers one of three questions. Naming the lens
makes the coverage explicit instead of implicit — nothing added, just labeled:

| Lens | Checks | Question answered |
|---|---|---|
| Input → output fidelity | Coverage, Correctness, Traceability | Does the deliverable say only, and all of, what validated knowledge (and by extension the source input) supports? |
| Output sufficiency | Template fidelity, Requirement quality, Consistency, Professional fitness, Uncertainty handling | Read on its own, is the deliverable structurally complete, unambiguous, internally consistent, and fit for its business/delivery purpose? |
| Best-practice / standards conformance | Standards conformance | Does the deliverable correctly apply the conventions, calculations, and governance rules captured from context/guidance sources — the rules for using facts, not just the facts themselves? |

Equal weighting across the nine checks holds each lens to account: no lens can
be satisfied by strength in another (e.g. a deliverable cannot compensate for
a standards-conformance defect by scoring well on template fidelity).

In the §2 Scorecard (report_grammar.md §5), group the nine dimension rows
under their lens using a bold, blank-score group-header row, in this fixed
order: input → output fidelity, output sufficiency, best-practice / standards
conformance. This keeps the grammar's fixed `| Dimension | Weight | Score | |`
columns unchanged — grouping is a row order and a header label, not a schema
change. In §3 Coverage & traceability, add one coverage-dimension row per
lens: source → deliverable coverage (input → output fidelity), a
self-sufficiency coverage row for the deliverable read on its own (output
sufficiency), and the standards/guidance-concepts-applied row already defined
(best-practice / standards conformance).

## Artifact intent

- BRD: explain business need, outcomes, scope, stakeholders, business rules,
  success measures, risks, and decisions.
- FRD: specify observable system behavior, interfaces, data behavior,
  constraints, and acceptance conditions without inventing design.
- URS: express user needs and verifiable outcomes at the level required by the
  selected template and evidenced governance context.
- Jira Story Pack: produce independently valuable work items with grounded
  actors, intent, acceptance criteria, dependencies, and traceability according
  to the selected Jira template or supplied framework.

Only apply a regulation, persona convention, verification method, issue field,
label scheme, estimation scheme, or document section when supported by evidence
or required by the selected template. Mark unsupported required fields as
insufficient input rather than filling them from package lore.

## Findings and gates

Every defect names its domain (`knowledge` or `output`), exact basis, impact,
and actionable remediation. Do not deduct for intentionally unselected outputs,
truthfully surfaced open items, template-authorized structure, or optional
duplication. A current critical evidence, correctness, standards-conformance, or missing-required-output defect blocks the gate. Informational observations do not reduce the score.
