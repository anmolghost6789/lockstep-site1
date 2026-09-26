# Workflow phases

DE Discovery's guided skill ([`skills/discover-project/SKILL.md`](../../skills/discover-project/SKILL.md)) runs a seven-phase method. The durable product of every phase is the OKF knowledge bundle under `knowledge/`, not the chat transcript.

| Stage | Purpose | Useful utility command(s) |
|---|---|---|
| Initialize | Create project state, evidence folders, and knowledge navigation. | `doctor`, `init` |
| Ingest | Hash, scan, snapshot, and extract supplied evidence. | `ingest` |
| Assess | Record observations, questions, approvals, and source-review decisions. | `register-observation`, `review-source` |
| Synthesize | Build or refresh the dynamic OKF knowledge navigation. | `rebuild-index` |
| Validate | Check the knowledge bundle and readiness profile. | `validate --profile` |
| Hand off | Export an approved ingestion specification when applicable. | `export-ingestion-config` |

## Phase 1 — Establish the minimum brief

Autonomous discovery may begin only once these are known, inferred from supplied evidence wherever possible before asking the user:

1. the outcome or decision discovery must enable;
2. a seed boundary — a business capability, named system, dataset, schema, or representative artifact;
3. the desired readiness target: `discovery-only`, `requirements-ready`, or `design-ready`;
4. the user's authority or owner for access and boundary expansion.

The engagement is classified into one or more archetypes in `.de-discovery.yaml` (see [project archetypes and facets](../../skills/discover-project/references/project-archetypes.md)), resolved into the smallest sufficient facet set. Unresolved blocking questions are persisted as an `open_questions` OKF concept rather than held in chat.

## Phase 2 — Register and normalize evidence

Every user-provided file or input directory is ingested (`ingest --path <path>`). The tool hashes exact bytes, scans for likely secrets, stores an immutable content-addressed snapshot, extracts supported text, and records a source revision. Unchanged inputs are skipped; changed bytes create a new revision — they never overwrite old evidence. Only the concepts linked to the changed revision (and their explicit dependents) are reconsidered, not the whole bundle.

Non-file observations — a URL, a Databricks result, an interview answer, or a decision — are recorded via `register-observation` with kind, title, source URI, and a redacted content file. Web evidence additionally requires `--publisher` and `--applicability`; see [research policy](../../skills/discover-project/references/research-policy.md).

## Phase 3 — Plan a bounded investigation

A `discovery_boundary` concept states included seeds/systems, explicit exclusions, read/profile/mutation permissions, breadth/depth limits, stop conditions, and the next expansion rule. Investigation follows a funnel: read seed evidence, gather narrow metadata around named assets, rank candidates by the scoring rubric in [discovery method](../../skills/discover-project/references/discovery-method.md), inspect only the shortlist, follow lineage/dependencies to the configured depth, and widen only for a documented evidence gap.

## Phase 4 — Inspect Databricks when in scope

Resolve the provider honestly — already configured AI Dev Kit MCP tools, then the Databricks CLI, then offline artifacts — per [Databricks access and autonomy](../../skills/discover-project/references/databricks-access.md). Every mutation is checked first with `authorize-action`; the run proceeds only on `ALLOW`, asks for approval on `ASK` (showing the exact resource, purpose, scope, and reversibility), and stops that path entirely on `DENY`. Agent-created resources are recorded with `record-resource`.

## Phase 5 — Synthesize the knowledge layer

Written concepts cover why the initiative exists, the bounded current-state systems and controls, business semantics and rules, constraints/risks/contradictions/unknowns, candidate target outcomes (clearly not facts), the evidence behind each material claim, and what was deliberately not investigated. See [OKF profile](../../skills/discover-project/references/okf-profile.md).

When the resolved facets include `acquisition`, this phase also creates the source-system profiles, acquisition contracts, and ingestion specifications described in [Inputs and outputs](inputs-and-outputs.md) and [source profiles, acquisition contracts, and ingestion specifications](../../skills/discover-project/references/acquisition-contract.md). When the archetypes include `migration-modernization`, it creates a migration assessment and dependency-aware migration units per [migration and modernization assessment](../../skills/discover-project/references/migration-assessment.md).

Exactly one `context_manifest` concept routes downstream agents (Requirements, Design, Build) to stable canonical IDs — not file paths — for the concepts each one needs.

Every pending source revision from Phase 2 must be assessed and given a disposition (`applied`, `reviewed-no-change`, or `out-of-scope`) via `review-source`; completion is refused while any revision remains unreviewed.

## Phase 6 — Assess readiness and stop

One `readiness_assessment` concept marks each criterion `supported`, `partial`, `missing`, or `not_applicable`, links supporting concepts, and names blocking gaps. See [evidence and readiness](../../skills/discover-project/references/evidence-and-readiness.md) for the exact criteria required at each readiness target. After the OKF profile validates, any implementation-ready ingestion configuration needed by Build is exported with `export-ingestion-config`.

Discovery stops when the requested readiness gate is supported, remaining unknowns are explicitly non-blocking or assigned, the boundary and exclusions are visible, no high-impact contradiction is hidden, and the context manifest routes downstream agents to the concepts they need — not when every available asset has been explored.

## Phase 7 — Validate and close

```powershell
python skills\discover-project\scripts\de_discovery.py rebuild-index --project-root PROJECT_ROOT
python skills\discover-project\scripts\de_discovery.py validate --project-root PROJECT_ROOT --profile
python skills\discover-project\scripts\de_discovery.py set-phase --project-root PROJECT_ROOT --phase complete --last-step "Validated OKF handoff"
```

If validation fails, the bundle is repaired and revalidated — the run never claims complete while validation fails or a requested readiness blocker remains. A newest-first dated entry is added to `knowledge/log.md` describing source revisions, material concept changes, boundary changes, readiness, and created resources.

The run closes by reporting the absolute path to `knowledge/index.md`, the readiness target and result, concepts changed by new evidence, unresolved blockers or contradictions, Databricks resources created or approvals still required, the research mode and material web evidence, and the validation result.
