# Traceability

Traceability is the linked relationship across three durable layers:

```text
source page -> topic entity -> RA-BLOCK in a final deliverable
```

- Source evidence uses relative Markdown links from each entity.
- Entity dependencies use relative links to stable-ID headings.
- `Deliverables:` declares which selected outputs consume an entity.
- Final documents list owned entity IDs in RA-BLOCK start markers.

Do not maintain a duplicate `traceability_map.json`. Derive coverage during
validation from current Markdown links and block markers. Persist only the final
evaluation projection at `outputs/03_evaluation/traceability.yaml` because it is
a reviewed output, not working state.

Fail evaluation for broken links, duplicate IDs, selected deliverables missing
applicable entities, or deliverable IDs absent from the knowledge layer. Report
removed entities as historical/remediated rather than silently reusing them.

## Independent evaluation projection

Do not derive source coverage solely from entity citations. Read each prepared
source evidence path and emit exactly one row per current source:

```yaml
meta:
  evaluation_id: "EVAL-..."
  snapshot:
    sources_sha256: "..."
    knowledge_sha256: "..."
    deliverables_sha256: "..."
source_coverage:
  - source_id: "SRC-001"
    source_sha256: "..."
    source_role: "semantic_evidence"
    evidence_checked: true
    knowledge_concepts: ["BR-001", "DEC-002"]
    status: "covered"
    disposition: "All material sections captured; footer is context only."
```

Allowed statuses are `covered`, `context_only`, `duplicate`, `superseded`,
`out_of_scope`, and `unresolved`. A source with no linked concepts is valid only
with a truthful non-`covered` status and an explicit disposition. The commit
guard verifies source IDs and hashes against the prepared evidence snapshot.
`semantic_evidence` requires source-to-concept coverage. Concepts derived from context/guidance sources retain their source role so the output pass can verify governance-conformance rather than re-deriving which concepts are standards-derived. A `control_input` such
as a template or branding asset is evaluated for correct application and uses
`context_only`; do not create a fake requirement entity merely to give it a
graph edge.

Keep entity-to-deliverable and cross-deliverable mappings in this file. Evaluate
them only after source coverage; they cannot prove knowledge completeness.
